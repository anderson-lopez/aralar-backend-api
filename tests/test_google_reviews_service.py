"""
Tests de `GoogleReviewsService`: sincronización idempotente, moderación
(automática y humana) y listado público.
"""
from datetime import datetime

import pytest

from aralar.core.reviews.providers import ReviewsProviderError
from aralar.repositories.google_reviews_repo import GoogleReviewsRepo
from aralar.services.google_reviews_service import GoogleReviewsService
from tests.factories import seed_google_review


class FakeProvider:
    name = "scraper"

    def __init__(self, reviews=None, error=None):
        self.reviews = reviews or []
        self.error = error
        self.calls = 0

    def fetch_reviews(self, *, tenant_id):
        self.calls += 1
        if self.error:
            raise self.error
        return self.reviews


def _incoming(external_id="review-1", rating=5, text="Muy bueno", name="Ana"):
    return {
        "external_id": external_id,
        "rating": rating,
        "text": text,
        "language": "es",
        "author": {"name": name, "photo_url": None, "profile_url": None},
        "published_at": datetime(2026, 7, 1, 10, 0, 0),
    }


def _svc(db, provider=None, min_rating=4):
    return GoogleReviewsService(GoogleReviewsRepo(db), provider=provider, min_rating=min_rating)


@pytest.mark.integration
class TestSync:
    def test_creates_new_reviews(self, db):
        svc = _svc(db, FakeProvider([_incoming("a"), _incoming("b", rating=3)]))
        res = svc.sync("aralar")

        assert res["fetched"] == 2
        assert res["created"] == 2
        assert res["auto_approved"] == 1
        assert res["pending"] == 1
        assert db["google_reviews"].count_documents({}) == 2

    def test_summary_counts_textless_reviews_as_rejected(self, db):
        svc = _svc(db, FakeProvider([
            _incoming("con-texto", rating=5, text="Muy bueno"),
            _incoming("sin-texto", rating=5, text=""),
        ]))
        res = svc.sync("aralar")

        assert res["auto_approved"] == 1
        assert res["auto_rejected"] == 1
        assert res["pending"] == 0
        # Se guardan igualmente: quedan recuperables desde el panel.
        assert db["google_reviews"].count_documents({}) == 2

    def test_textless_reviews_never_reach_the_landing(self, db):
        svc = _svc(db, FakeProvider([_incoming("sin-texto", rating=5, text="")]))
        svc.sync("aralar")
        assert svc.public_list("aralar")["total"] == 0

    def test_rerunning_does_not_duplicate(self, db):
        provider = FakeProvider([_incoming("a")])
        svc = _svc(db, provider)

        svc.sync("aralar")
        second = svc.sync("aralar")

        assert db["google_reviews"].count_documents({}) == 1
        assert second["created"] == 0
        assert second["updated"] == 1

    def test_updates_content_of_existing_review(self, db):
        svc = _svc(db, FakeProvider([_incoming("a", text="Primera versión")]))
        svc.sync("aralar")

        svc.provider = FakeProvider([_incoming("a", text="Texto corregido", rating=4)])
        svc.sync("aralar")

        stored = db["google_reviews"].find_one({"external_id": "a"})
        assert stored["text"] == "Texto corregido"
        assert stored["rating"] == 4
        assert db["google_reviews"].count_documents({}) == 1

    def test_review_without_external_id_is_ignored(self, db):
        svc = _svc(db, FakeProvider([{"rating": 5, "text": "sin id"}]))
        res = svc.sync("aralar")
        assert res["created"] == 0
        assert db["google_reviews"].count_documents({}) == 0

    def test_same_external_id_is_isolated_per_tenant(self, db):
        svc = _svc(db, FakeProvider([_incoming("a")]))
        svc.sync("aralar")
        svc.sync("otro-tenant")
        assert db["google_reviews"].count_documents({}) == 2


@pytest.mark.integration
class TestSyncNeverBreaksTheLanding:
    def test_provider_error_is_reported_not_raised(self, db):
        svc = _svc(db, FakeProvider(error=ReviewsProviderError("rate limited")))
        res = svc.sync("aralar")

        assert res["errors"] == ["rate limited"]
        assert res["fetched"] == 0

    def test_previous_data_survives_a_failed_sync(self, db):
        seed_google_review(db, external_id="vieja", text="Sigo aquí")
        svc = _svc(db, FakeProvider(error=ReviewsProviderError("boom")))

        svc.sync("aralar")

        assert db["google_reviews"].count_documents({}) == 1
        assert svc.public_list("aralar")["total"] == 1

    def test_unexpected_provider_exception_is_contained(self, db):
        svc = _svc(db, FakeProvider(error=RuntimeError("formato inesperado")))
        res = svc.sync("aralar")
        assert "unexpected provider failure" in res["errors"][0]

    def test_without_provider_reports_error(self, db):
        res = _svc(db, None).sync("aralar")
        assert res["errors"] == ["no provider configured"]


@pytest.mark.integration
class TestHumanDecisionWins:
    def test_sync_does_not_resurrect_a_rejected_review(self, db):
        """El caso que importa: algo rechazado a mano no puede volver a la landing."""
        svc = _svc(db, FakeProvider([_incoming("a", rating=5)]))
        svc.sync("aralar")

        stored = db["google_reviews"].find_one({"external_id": "a"})
        svc.moderate(str(stored["_id"]), "rejected", user_id="u1")

        svc.sync("aralar")

        after = db["google_reviews"].find_one({"external_id": "a"})
        assert after["status"] == "rejected"
        assert after["moderation"]["auto"] is False
        assert after["moderation"]["by"] == "u1"

    def test_sync_refreshes_content_even_when_human_decided(self, db):
        svc = _svc(db, FakeProvider([_incoming("a", text="Original")]))
        svc.sync("aralar")
        stored = db["google_reviews"].find_one({"external_id": "a"})
        svc.moderate(str(stored["_id"]), "rejected", user_id="u1")

        svc.provider = FakeProvider([_incoming("a", text="Editada por el autor")])
        svc.sync("aralar")

        after = db["google_reviews"].find_one({"external_id": "a"})
        assert after["text"] == "Editada por el autor"
        assert after["status"] == "rejected"

    def test_automatic_decision_is_re_evaluated_on_sync(self, db):
        svc = _svc(db, FakeProvider([_incoming("a", rating=2)]))
        svc.sync("aralar")
        assert db["google_reviews"].find_one({"external_id": "a"})["status"] == "pending"

        svc.provider = FakeProvider([_incoming("a", rating=5)])
        svc.sync("aralar")
        assert db["google_reviews"].find_one({"external_id": "a"})["status"] == "approved"


@pytest.mark.unit
class TestAutoModeration:
    @pytest.mark.parametrize("rating,expected", [(5, "approved"), (4, "approved"), (3, "pending"), (1, "pending")])
    def test_threshold(self, db, rating, expected):
        svc = _svc(db)
        status, _ = svc._auto_moderate({"rating": rating, "text": "algo"})
        assert status == expected

    def test_empty_text_is_auto_rejected_even_with_five_stars(self, db):
        """~44% de las reseñas de Google son solo estrellas: si fuesen a `pending`
        ahogarían la bandeja con items que nunca se van a poder publicar."""
        status, reason = _svc(db)._auto_moderate({"rating": 5, "text": "   "})
        assert status == "rejected"
        assert "empty text" in reason

    def test_low_rating_with_text_needs_a_human(self, db):
        status, _ = _svc(db)._auto_moderate({"rating": 2, "text": "Tardaron mucho"})
        assert status == "pending"

    def test_missing_rating_stays_pending(self, db):
        status, reason = _svc(db)._auto_moderate({"rating": None, "text": "algo"})
        assert status == "pending"
        assert reason == "missing rating"

    def test_threshold_is_configurable(self, db):
        svc = _svc(db, min_rating=5)
        assert svc._auto_moderate({"rating": 4, "text": "algo"})[0] == "pending"
        assert svc._auto_moderate({"rating": 5, "text": "algo"})[0] == "approved"


@pytest.mark.integration
class TestModerate:
    def test_marks_decision_as_human(self, db):
        rid = str(seed_google_review(db, status="pending")["_id"])
        res = _svc(db).moderate(rid, "approved", user_id="u9")
        assert res["status"] == "approved"
        assert res["moderation"]["auto"] is False
        assert res["moderation"]["by"] == "u9"

    def test_rejects_invalid_status(self, db):
        rid = str(seed_google_review(db)["_id"])
        assert "error" in _svc(db).moderate(rid, "quizas")

    def test_returns_none_when_not_found(self, db):
        from bson import ObjectId

        assert _svc(db).moderate(str(ObjectId()), "approved") is None


@pytest.mark.integration
class TestCreateManual:
    def test_creates_and_auto_approves(self, db):
        res = _svc(db).create_manual(
            {"tenant_id": "aralar", "rating": 5, "text": "Genial", "author": {"name": "Ana"}}
        )
        assert res["status"] == "approved"
        assert res["provider"] == "manual"
        assert res["external_id"].startswith("manual-")

    def test_low_rating_goes_to_pending(self, db):
        res = _svc(db).create_manual({"tenant_id": "aralar", "rating": 2, "text": "Meh"})
        assert res["status"] == "pending"

    def test_duplicate_external_id_conflicts(self, db):
        svc = _svc(db)
        payload = {"tenant_id": "aralar", "rating": 5, "text": "Uno", "external_id": "fijo"}
        svc.create_manual(payload)
        assert "conflict" in svc.create_manual(dict(payload))


@pytest.mark.integration
class TestPublicList:
    def test_only_returns_approved(self, db):
        seed_google_review(db, external_id="ok", status="approved")
        seed_google_review(db, external_id="pend", status="pending")
        seed_google_review(db, external_id="rej", status="rejected")

        res = _svc(db).public_list("aralar")
        assert res["total"] == 1
        assert res["items"][0]["text"]

    def test_computes_average_rating(self, db):
        seed_google_review(db, external_id="a", rating=5)
        seed_google_review(db, external_id="b", rating=4)
        assert _svc(db).public_list("aralar")["average_rating"] == 4.5

    def test_average_is_none_without_reviews(self, db):
        assert _svc(db).public_list("aralar")["average_rating"] is None

    def test_display_order_nulls_go_last(self, db):
        """Mongo pone los null primero al ordenar asc; aquí deben ir al final."""
        seed_google_review(db, external_id="sin-orden", display_order=None, text="C")
        seed_google_review(db, external_id="segunda", display_order=2, text="B")
        seed_google_review(db, external_id="primera", display_order=1, text="A")

        items = _svc(db).public_list("aralar")["items"]
        assert [i["text"] for i in items] == ["A", "B", "C"]

    def test_ties_break_by_published_at_desc(self, db):
        seed_google_review(
            db, external_id="vieja", display_order=None, published_at=datetime(2026, 1, 1)
        )
        seed_google_review(
            db, external_id="nueva", display_order=None, published_at=datetime(2026, 7, 1)
        )
        raw = sorted(db["google_reviews"].find({}), key=GoogleReviewsService._public_sort_key)
        assert [r["external_id"] for r in raw] == ["nueva", "vieja"]

    def test_limit_truncates_items_but_not_total(self, db):
        for i in range(5):
            seed_google_review(db, external_id=f"r{i}")
        res = _svc(db).public_list("aralar", limit=2)
        assert len(res["items"]) == 2
        assert res["total"] == 5

    def test_exposes_author_attribution_fields(self, db):
        seed_google_review(db)
        item = _svc(db).public_list("aralar")["items"][0]
        assert item["author_name"] == "Ana García"
        assert item["author_photo_url"].startswith("https://lh3.googleusercontent.com/")
        assert item["author_profile_url"].startswith("https://www.google.com/maps/contrib/")

    def test_filters_by_tenant(self, db):
        seed_google_review(db, external_id="a", tenant_id="aralar")
        seed_google_review(db, external_id="b", tenant_id="otro")
        assert _svc(db).public_list("aralar")["total"] == 1


@pytest.mark.integration
class TestListAndUpdate:
    def test_filters_by_status(self, db):
        seed_google_review(db, external_id="a", status="approved")
        seed_google_review(db, external_id="b", status="pending")
        res = _svc(db).list({"status": "pending"})
        assert res["total"] == 1

    def test_update_only_touches_presentation(self, db):
        rid = str(seed_google_review(db, rating=5)["_id"])
        res = _svc(db).update(rid, {"is_featured": True, "rating": 1, "status": "rejected"})
        assert res["is_featured"] is True
        assert res["rating"] == 5           # el contenido no se toca
        assert res["status"] == "approved"  # el estado solo cambia por /moderate

    def test_delete_removes_review(self, db):
        rid = str(seed_google_review(db)["_id"])
        assert _svc(db).delete(rid) == {"ok": True}
        assert db["google_reviews"].count_documents({}) == 0
