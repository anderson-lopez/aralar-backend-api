"""
Tests del provider de reseñas (`aralar/core/reviews/providers.py`).

`requests` va siempre mockeado: ningún test toca la red.

El fixture `tests/fixtures/google_reviews_response.json` reproduce la forma de la
respuesta del endpoint interno de Google Maps. Si Google cambia el formato, este
fixture y `_parse_review` son lo único que hay que tocar.
"""
import json
import os
from datetime import datetime
from unittest.mock import patch

import pytest

from aralar.core.reviews.providers import (
    GoogleMapsScraperProvider,
    ManualProvider,
    ReviewsProviderError,
    get_provider,
)

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "google_reviews_response.json")

with open(FIXTURE_PATH, encoding="utf-8") as fh:
    FIXTURE_PAGE = json.load(fh)

# Ids reales del fixture (Google los devuelve en base64).
ID_ANA = "Ci9DQUlRQUNvZENodHljRjlvT21KSVNYbDRNRU54TUZaSE5UTldXemx5TjI5SmRVRRAB"
ID_LUIS = "ChdDSUhNMG9nS0VJQ0FnSUNkbnVIUzZRRRAB"
ID_MARTA = "ChZDSUhNMG9nS0VJQ0FnSUNkbnVIUzZREAE"


def _response_text(payload, with_prefix=True):
    body = json.dumps(payload, ensure_ascii=False)
    return ")]}'\n" + body if with_prefix else body


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


@pytest.mark.unit
class TestGetProvider:
    def test_defaults_to_manual(self):
        assert get_provider({}).name == "manual"

    def test_unknown_provider_falls_back_to_manual(self):
        assert get_provider({"GOOGLE_REVIEWS_PROVIDER": "nope"}).name == "manual"

    def test_selects_scraper(self):
        p = get_provider(
            {"GOOGLE_REVIEWS_PROVIDER": "scraper", "GOOGLE_MAPS_FEATURE_ID": "0x1:0x2"}
        )
        assert p.name == "scraper"
        assert p.feature_id == "0x1:0x2"

    def test_manual_provider_returns_nothing(self):
        assert ManualProvider().fetch_reviews(tenant_id="aralar") == []


@pytest.mark.unit
class TestFeatureIdExtraction:
    def test_extracts_from_place_url(self):
        url = (
            "https://www.google.com/maps/place/Aralar/@43.31,-1.98,17z/"
            "data=!3m1!4b1!4m6!3m5!1s0xd51a5b8ff123456:0xabc987654321def!8m2!3d43.31!4d-1.98"
        )
        assert (
            GoogleMapsScraperProvider.extract_feature_id(url)
            == "0xd51a5b8ff123456:0xabc987654321def"
        )

    def test_returns_empty_when_absent(self):
        assert GoogleMapsScraperProvider.extract_feature_id("https://example.com") == ""
        assert GoogleMapsScraperProvider.extract_feature_id("") == ""

    def test_place_url_is_used_when_feature_id_missing(self):
        p = GoogleMapsScraperProvider(place_url="https://maps.google.com/?q=!1s0xaaa:0xbbb")
        assert p.feature_id == "0xaaa:0xbbb"

    def test_fetch_without_feature_id_raises_controlled_error(self):
        p = GoogleMapsScraperProvider()
        with pytest.raises(ReviewsProviderError, match="missing feature id"):
            p.fetch_reviews(tenant_id="aralar")


@pytest.mark.unit
class TestPayloadDecoding:
    def test_strips_anti_hijacking_prefix(self):
        payload = GoogleMapsScraperProvider._load_payload(")]}'\n[1, 2, 3]")
        assert payload == [1, 2, 3]

    def test_decodes_without_prefix(self):
        assert GoogleMapsScraperProvider._load_payload("[1, 2]") == [1, 2]

    def test_empty_response_raises(self):
        with pytest.raises(ReviewsProviderError, match="empty response"):
            GoogleMapsScraperProvider._load_payload("")

    def test_garbage_raises_controlled_error(self):
        with pytest.raises(ReviewsProviderError, match="could not decode"):
            GoogleMapsScraperProvider._load_payload("<html>bloqueado</html>")


@pytest.mark.unit
class TestParsing:
    def test_parses_fixture_fields(self):
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        reviews, token = provider._parse_page(_response_text(FIXTURE_PAGE))

        assert token == "TOKEN_PAGINA_2"
        assert len(reviews) == 3

        first = reviews[0]
        assert first["external_id"] == ID_ANA
        assert first["rating"] == 5
        assert first["text"] == "Excelente comida y trato inmejorable. Volveremos sin duda."
        assert first["language"] == "es"
        assert first["author"]["name"] == "Ana Garcia"
        assert first["author"]["photo_url"].startswith("https://lh3.googleusercontent.com/")
        assert first["author"]["profile_url"].startswith("https://www.google.com/maps/contrib/")
        assert isinstance(first["published_at"], datetime)

    def test_prefers_full_text_over_truncated_preview(self):
        """Google manda el texto íntegro en r[27] y un recorte en r[28]."""
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        reviews, _ = provider._parse_page(_response_text(FIXTURE_PAGE))
        luis = [r for r in reviews if r["external_id"] == ID_LUIS][0]
        assert luis["text"] == "Muy buena relacion calidad precio. El menu del dia esta muy bien."

    def test_parses_low_rating_review(self):
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        reviews, _ = provider._parse_page(_response_text(FIXTURE_PAGE))
        low = [r for r in reviews if r["external_id"] == ID_MARTA][0]
        assert low["rating"] == 2

    def test_malformed_review_is_skipped_without_breaking_batch(self):
        payload = _page([_review_node("ok-id", 5, "Bien"), "no-soy-una-lista", 12345])
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        reviews, _ = provider._parse_page(_response_text(payload))
        # Los nodos inválidos se descartan; no se propaga ninguna excepción.
        assert [r["external_id"] for r in reviews] == ["ok-id"]

    def test_review_without_rating_is_discarded(self):
        node = [None] * 48
        node[5] = "solo-id"
        assert GoogleMapsScraperProvider._parse_review(node) is None

    def test_non_list_node_is_discarded(self):
        assert GoogleMapsScraperProvider._parse_review("texto") is None
        assert GoogleMapsScraperProvider._parse_review([]) is None


@pytest.mark.unit
class TestPagination:
    def test_follows_next_page_token(self):
        page2 = _page([_review_node("review-ddd", 5, "Segunda página")])
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2", pause_seconds=0)

        responses = [
            FakeResponse(_response_text(FIXTURE_PAGE)),
            FakeResponse(_response_text(page2)),
        ]
        with patch("aralar.core.reviews.providers.requests.get", side_effect=responses):
            reviews = provider.fetch_reviews(tenant_id="aralar")

        ids = [r["external_id"] for r in reviews]
        assert ids == [ID_ANA, ID_LUIS, ID_MARTA, "review-ddd"]

    def test_sends_pagination_token_on_second_request(self):
        """La segunda petición debe llevar el token; si no, se repetiría la página 1."""
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2", pause_seconds=0)
        page2 = _page([_review_node("review-ddd", 5, "Segunda")])

        with patch(
            "aralar.core.reviews.providers.requests.get",
            side_effect=[
                FakeResponse(_response_text(FIXTURE_PAGE)),
                FakeResponse(_response_text(page2)),
            ],
        ) as mocked:
            provider.fetch_reviews(tenant_id="aralar")

        primera = mocked.call_args_list[0].kwargs["params"]["reqpld"]
        segunda = mocked.call_args_list[1].kwargs["params"]["reqpld"]
        assert "TOKEN_PAGINA_2" not in primera
        assert "TOKEN_PAGINA_2" in segunda

    def test_stops_at_max_pages(self):
        # Cada página devuelve reseñas nuevas y token: solo el límite corta el bucle.
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2", max_pages=2, pause_seconds=0)
        counter = {"n": 0}

        def _fake_get(*_args, **_kwargs):
            counter["n"] += 1
            page = _page([_review_node(f"review-{counter['n']}", 5, "Texto")], token="SIGUIENTE")
            return FakeResponse(_response_text(page))

        with patch("aralar.core.reviews.providers.requests.get", side_effect=_fake_get):
            reviews = provider.fetch_reviews(tenant_id="aralar")

        assert counter["n"] == 2
        assert len(reviews) == 2

    def test_stops_when_no_new_reviews(self):
        """Si Google repite la misma página, el bucle corta en vez de girar en vacío."""
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2", max_pages=5, pause_seconds=0)
        page = _page([_review_node("review-repetida", 5, "Texto")], token="SIEMPRE_EL_MISMO")

        with patch(
            "aralar.core.reviews.providers.requests.get",
            return_value=FakeResponse(_response_text(page)),
        ) as mocked:
            reviews = provider.fetch_reviews(tenant_id="aralar")

        assert len(reviews) == 1
        assert mocked.call_count == 2  # la segunda no aporta nada y corta

    def test_deduplicates_across_pages(self):
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2", pause_seconds=0)
        page1 = _page(
            [_review_node("dup", 5, "Uno"), _review_node("otra", 4, "Dos")], token="T2"
        )
        page2 = _page([_review_node("dup", 5, "Uno")])

        with patch(
            "aralar.core.reviews.providers.requests.get",
            side_effect=[FakeResponse(_response_text(page1)), FakeResponse(_response_text(page2))],
        ):
            reviews = provider.fetch_reviews(tenant_id="aralar")

        assert [r["external_id"] for r in reviews] == ["dup", "otra"]


@pytest.mark.unit
class TestNetworkErrors:
    def test_http_429_is_reported_as_rate_limit(self):
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        with patch(
            "aralar.core.reviews.providers.requests.get",
            return_value=FakeResponse("", status_code=429),
        ):
            with pytest.raises(ReviewsProviderError, match="rate limited"):
                provider.fetch_reviews(tenant_id="aralar")

    def test_unexpected_status_is_reported(self):
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        with patch(
            "aralar.core.reviews.providers.requests.get",
            return_value=FakeResponse("", status_code=503),
        ):
            with pytest.raises(ReviewsProviderError, match="unexpected HTTP status 503"):
                provider.fetch_reviews(tenant_id="aralar")

    def test_connection_error_is_wrapped(self):
        import requests as requests_lib

        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2")
        with patch(
            "aralar.core.reviews.providers.requests.get",
            side_effect=requests_lib.Timeout("timed out"),
        ):
            with pytest.raises(ReviewsProviderError, match="request to Google Maps failed"):
                provider.fetch_reviews(tenant_id="aralar")

    def test_request_uses_explicit_timeout(self):
        provider = GoogleMapsScraperProvider(feature_id="0x1:0x2", timeout=7)
        with patch(
            "aralar.core.reviews.providers.requests.get",
            return_value=FakeResponse(_response_text([None, "", []])),
        ) as mocked:
            provider.fetch_reviews(tenant_id="aralar")
        assert mocked.call_args.kwargs["timeout"] == 7


def _review_node(external_id, rating, text, name="Autor Test", epoch_ms="1783000000000"):
    """Nodo de reseña con la estructura real de Google (48 campos).

    Solo se rellenan los índices que consume `_parse_review`; el resto va a `None`,
    igual que en la respuesta real.
    """
    r = [None] * 48
    r[1] = rating
    r[2] = ["Hace 1 mes", None, epoch_ms]
    r[3] = [
        name,
        "https://lh3.googleusercontent.com/a/test",
        "https://www.google.com/maps/contrib/999/reviews?hl=es",
        127,
        581,
        [],
    ]
    r[5] = external_id
    r[26] = "es"
    r[27] = text
    r[28] = text[:60]
    r[45] = rating
    r[46] = 5
    return r


def _page(reviews, token=""):
    """Envoltorio de página: reseñas en data[1][10][2], token en data[1][10][6]."""
    container = [None, None, reviews, None, None, None, token]
    return [None, [None, None, None, None, None, None, None, None, None, None, container]]
