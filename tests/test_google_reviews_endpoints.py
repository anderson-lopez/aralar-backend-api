"""
Tests E2E de los endpoints de reseñas (/api/google-reviews).

Cubren el endpoint público de la landing, la bandeja de moderación, el CRUD
autenticado y los permisos (401/403).
"""
from bson import ObjectId
import pytest

from tests.factories import seed_google_review


@pytest.mark.e2e
class TestPublicReviews:
    def test_is_open_without_token(self, client, db):
        seed_google_review(db)
        res = client.get("/api/google-reviews/public")
        assert res.status_code == 200

    def test_returns_only_approved(self, client, db):
        seed_google_review(db, external_id="ok", status="approved")
        seed_google_review(db, external_id="pend", status="pending")
        seed_google_review(db, external_id="rej", status="rejected")

        res = client.get("/api/google-reviews/public?tenant_id=aralar")
        assert res.json["total"] == 1

    def test_includes_average_rating(self, client, db):
        seed_google_review(db, external_id="a", rating=5)
        seed_google_review(db, external_id="b", rating=4)
        res = client.get("/api/google-reviews/public?tenant_id=aralar")
        assert res.json["average_rating"] == 4.5

    def test_exposes_attribution_fields(self, client, db):
        seed_google_review(db)
        item = client.get("/api/google-reviews/public").json["items"][0]
        assert item["author_name"] == "Ana García"
        assert "author_photo_url" in item
        assert "author_profile_url" in item

    def test_respects_limit(self, client, db):
        for i in range(4):
            seed_google_review(db, external_id=f"r{i}")
        res = client.get("/api/google-reviews/public?limit=2")
        assert len(res.json["items"]) == 2
        assert res.json["total"] == 4

    def test_empty_when_no_reviews(self, client):
        res = client.get("/api/google-reviews/public")
        assert res.status_code == 200
        assert res.json["items"] == []
        assert res.json["average_rating"] is None


@pytest.mark.e2e
class TestListReviews:
    def test_lists_with_permission(self, client, db, auth_headers):
        seed_google_review(db)
        res = client.get("/api/google-reviews", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["total"] == 1

    def test_moderation_inbox_filters_by_status(self, client, db, auth_headers):
        seed_google_review(db, external_id="a", status="approved")
        seed_google_review(db, external_id="b", status="pending")
        res = client.get("/api/google-reviews?status=pending", headers=auth_headers())
        assert res.json["total"] == 1

    def test_requires_auth(self, client):
        assert client.get("/api/google-reviews").status_code == 401

    def test_forbidden_without_permission(self, client, auth_headers):
        res = client.get("/api/google-reviews", headers=auth_headers(permissions=["menus:read"]))
        assert res.status_code == 403

    def test_get_by_id(self, client, db, auth_headers):
        rid = str(seed_google_review(db)["_id"])
        res = client.get(f"/api/google-reviews/{rid}", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["external_id"] == "review-1"

    def test_invalid_id_returns_400(self, client, auth_headers):
        res = client.get("/api/google-reviews/no-es-un-id", headers=auth_headers())
        assert res.status_code == 400

    def test_missing_id_returns_404(self, client, auth_headers):
        res = client.get(f"/api/google-reviews/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404


@pytest.mark.e2e
class TestCreateManual:
    def test_creates_and_auto_approves(self, client, auth_headers):
        res = client.post(
            "/api/google-reviews/manual",
            json={
                "tenant_id": "aralar",
                "rating": 5,
                "text": "Excelente",
                "author": {"name": "Ana"},
            },
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert res.json["status"] == "approved"
        assert res.json["provider"] == "manual"

    def test_low_rating_goes_to_pending(self, client, auth_headers):
        res = client.post(
            "/api/google-reviews/manual",
            json={"tenant_id": "aralar", "rating": 2, "text": "Malo"},
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert res.json["status"] == "pending"

    def test_rating_out_of_range_is_422(self, client, auth_headers):
        res = client.post(
            "/api/google-reviews/manual",
            json={"tenant_id": "aralar", "rating": 9, "text": "x"},
            headers=auth_headers(),
        )
        assert res.status_code == 422

    def test_duplicate_external_id_returns_409(self, client, auth_headers):
        payload = {"tenant_id": "aralar", "rating": 5, "text": "Uno", "external_id": "fijo"}
        client.post("/api/google-reviews/manual", json=payload, headers=auth_headers())
        res = client.post("/api/google-reviews/manual", json=payload, headers=auth_headers())
        assert res.status_code == 409

    def test_requires_auth(self, client):
        res = client.post(
            "/api/google-reviews/manual", json={"tenant_id": "aralar", "rating": 5}
        )
        assert res.status_code == 401


@pytest.mark.e2e
class TestModerateEndpoint:
    def test_approves_pending_review(self, client, db, auth_headers):
        rid = str(seed_google_review(db, status="pending")["_id"])
        res = client.put(
            f"/api/google-reviews/{rid}/moderate",
            json={"status": "approved"},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        assert res.json["status"] == "approved"
        assert res.json["moderation"]["auto"] is False

    def test_rejected_review_disappears_from_public(self, client, db, auth_headers):
        rid = str(seed_google_review(db, status="approved")["_id"])
        assert client.get("/api/google-reviews/public").json["total"] == 1

        client.put(
            f"/api/google-reviews/{rid}/moderate",
            json={"status": "rejected"},
            headers=auth_headers(),
        )
        assert client.get("/api/google-reviews/public").json["total"] == 0

    def test_invalid_status_is_422(self, client, db, auth_headers):
        rid = str(seed_google_review(db)["_id"])
        res = client.put(
            f"/api/google-reviews/{rid}/moderate",
            json={"status": "quizas"},
            headers=auth_headers(),
        )
        assert res.status_code == 422

    def test_forbidden_without_moderate_permission(self, client, db, auth_headers):
        rid = str(seed_google_review(db)["_id"])
        res = client.put(
            f"/api/google-reviews/{rid}/moderate",
            json={"status": "approved"},
            headers=auth_headers(permissions=["google_reviews:read"]),
        )
        assert res.status_code == 403


@pytest.mark.e2e
class TestUpdateAndDelete:
    def test_updates_presentation_fields(self, client, db, auth_headers):
        rid = str(seed_google_review(db)["_id"])
        res = client.put(
            f"/api/google-reviews/{rid}",
            json={"is_featured": True, "display_order": 3},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        assert res.json["is_featured"] is True
        assert res.json["display_order"] == 3

    def test_cannot_change_status_through_update(self, client, db, auth_headers):
        rid = str(seed_google_review(db, status="approved")["_id"])
        res = client.put(
            f"/api/google-reviews/{rid}",
            json={"status": "rejected"},
            headers=auth_headers(),
        )
        # `status` no está en el schema de update: se rechaza explícitamente.
        assert res.status_code == 422
        assert db["google_reviews"].find_one({"_id": ObjectId(rid)})["status"] == "approved"

    def test_deletes_review(self, client, db, auth_headers):
        rid = str(seed_google_review(db)["_id"])
        res = client.delete(f"/api/google-reviews/{rid}", headers=auth_headers())
        assert res.status_code == 200
        assert db["google_reviews"].count_documents({}) == 0

    def test_delete_requires_permission(self, client, db, auth_headers):
        rid = str(seed_google_review(db)["_id"])
        res = client.delete(
            f"/api/google-reviews/{rid}", headers=auth_headers(permissions=["google_reviews:read"])
        )
        assert res.status_code == 403


@pytest.mark.e2e
class TestSyncEndpoint:
    def test_manual_provider_returns_empty_summary(self, client, auth_headers):
        res = client.post("/api/google-reviews/sync", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["fetched"] == 0
        assert res.json["errors"] == []

    def test_requires_sync_permission(self, client, auth_headers):
        res = client.post(
            "/api/google-reviews/sync", headers=auth_headers(permissions=["google_reviews:read"])
        )
        assert res.status_code == 403

    def test_requires_auth(self, client):
        assert client.post("/api/google-reviews/sync").status_code == 401
