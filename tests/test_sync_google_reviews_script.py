"""
Tests del script `scripts/sync_google_reviews.py`.

Cubren sobre todo el gate `--if-empty`, que es lo que ejecutan `docker-start.bat`
y `docker-start.sh` **en cada arranque**: tiene que traer las reseñas la primera vez
y no volver a consultar a Google en los arranques siguientes.
"""
import importlib.util
import os
import sys
from unittest.mock import patch

import mongomock
import pytest

SCRIPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "scripts", "sync_google_reviews.py"
)


def _load_script():
    """Carga el script como módulo (vive en scripts/, fuera del paquete `aralar`)."""
    spec = importlib.util.spec_from_file_location("sync_google_reviews", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sync_script = _load_script()


INCOMING = [
    {
        "external_id": "r1",
        "rating": 5,
        "text": "Muy bueno",
        "language": "es",
        "author": {"name": "Ana", "photo_url": None, "profile_url": None},
        "published_at": None,
    }
]


class SpyProvider:
    """Cuenta cuántas veces se ha llamado al origen."""

    name = "scraper"

    def __init__(self):
        self.calls = 0

    def fetch_reviews(self, *, tenant_id):
        self.calls += 1
        return list(INCOMING)


@pytest.fixture
def mongo():
    return mongomock.MongoClient("mongodb://localhost:27017/aralar")


def _run(argv, mongo_client, provider):
    with patch.object(sys, "argv", ["sync_google_reviews.py"] + argv), patch.object(
        sync_script, "MongoClient", return_value=mongo_client
    ), patch.object(sync_script, "get_provider", return_value=provider):
        return sync_script.main()


@pytest.mark.integration
class TestIfEmptyGate:
    def test_syncs_when_collection_is_empty(self, mongo):
        provider = SpyProvider()
        code = _run(["--if-empty"], mongo, provider)

        assert code == 0
        assert provider.calls == 1
        assert mongo["aralar"]["google_reviews"].count_documents({}) == 1

    def test_does_not_touch_google_when_reviews_already_exist(self, mongo):
        """El caso que justifica el flag: arrancar Docker 20 veces no son 20 scrapes."""
        provider = SpyProvider()
        _run(["--if-empty"], mongo, provider)
        code = _run(["--if-empty"], mongo, provider)

        assert code == 0
        assert provider.calls == 1  # la segunda vez ni consulta

    def test_without_the_flag_it_always_syncs(self, mongo):
        provider = SpyProvider()
        _run([], mongo, provider)
        _run([], mongo, provider)

        assert provider.calls == 2
        # Sigue siendo idempotente: el upsert no duplica.
        assert mongo["aralar"]["google_reviews"].count_documents({}) == 1

    def test_gate_is_per_tenant(self, mongo):
        provider = SpyProvider()
        _run(["--if-empty", "--tenant", "aralar"], mongo, provider)
        _run(["--if-empty", "--tenant", "otro"], mongo, provider)

        assert provider.calls == 2
        assert mongo["aralar"]["google_reviews"].count_documents({}) == 2


@pytest.mark.integration
class TestStartupIsNeverBlocked:
    def test_unreachable_mongo_exits_cleanly(self, mongo):
        """Sin Mongo el script sale con código 1, pero sin traceback: los scripts de
        arranque lo tratan como aviso y la API levanta igual."""
        provider = SpyProvider()
        with patch.object(sys, "argv", ["sync_google_reviews.py", "--if-empty"]), patch.object(
            sync_script, "MongoClient", side_effect=Exception("connection refused")
        ), patch.object(sync_script, "get_provider", return_value=provider):
            code = sync_script.main()

        assert code == 1
        assert provider.calls == 0

    def test_provider_failure_reports_error_without_raising(self, mongo):
        from aralar.core.reviews.providers import ReviewsProviderError

        class BrokenProvider:
            name = "scraper"

            def fetch_reviews(self, *, tenant_id):
                raise ReviewsProviderError("rate limited by Google (HTTP 429)")

        code = _run(["--if-empty"], mongo, BrokenProvider())
        assert code == 1  # cron lo detecta, pero no hay excepción sin capturar

    def test_manual_provider_is_a_harmless_noop(self, mongo):
        """Config por defecto (sin URL): el arranque no debe fallar ni escribir nada."""
        from aralar.core.reviews.providers import ManualProvider

        code = _run(["--if-empty"], mongo, ManualProvider())
        assert code == 0
        assert mongo["aralar"]["google_reviews"].count_documents({}) == 0
