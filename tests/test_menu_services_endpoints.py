"""
Tests E2E de los endpoints de `menu_services` (/api/menu-services).

Cubren CRUD autenticado, permisos (401/403), conflictos (409), y el endpoint
público `/public` que alimenta la sección "Otros servicios".
"""
import pytest

from tests.factories import seed_menu_service, seed_menu


@pytest.mark.e2e
class TestCreateService:
    def test_creates_service(self, client, auth_headers):
        res = client.post(
            "/api/menu-services",
            json={"tenant_id": "aralar", "slug": "desayunos", "name": "Desayunos"},
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert res.json["slug"] == "desayunos"

    def test_requires_auth(self, client):
        res = client.post(
            "/api/menu-services",
            json={"tenant_id": "aralar", "slug": "desayunos", "name": "Desayunos"},
        )
        assert res.status_code == 401

    def test_forbidden_without_permission(self, client, auth_headers):
        res = client.post(
            "/api/menu-services",
            json={"tenant_id": "aralar", "slug": "desayunos", "name": "Desayunos"},
            headers=auth_headers(permissions=["menus:read"]),
        )
        assert res.status_code == 403

    def test_duplicate_slug_returns_409(self, client, db, auth_headers):
        seed_menu_service(db, slug="desayunos")
        res = client.post(
            "/api/menu-services",
            json={"tenant_id": "aralar", "slug": "desayunos", "name": "Otro"},
            headers=auth_headers(),
        )
        assert res.status_code == 409


@pytest.mark.e2e
class TestListAndGetService:
    def test_lists_services(self, client, db, auth_headers):
        seed_menu_service(db, slug="desayunos")
        res = client.get("/api/menu-services", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["total"] == 1

    def test_get_by_id(self, client, db, auth_headers):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = client.get(f"/api/menu-services/{sid}", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["slug"] == "desayunos"

    def test_get_404_when_missing(self, client, auth_headers):
        from bson import ObjectId
        res = client.get(f"/api/menu-services/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404


@pytest.mark.e2e
class TestUpdateService:
    def test_updates_service(self, client, db, auth_headers):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = client.put(
            f"/api/menu-services/{sid}",
            json={"name": "Nuevo", "order": 5},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        assert res.json["name"] == "Nuevo"
        assert res.json["order"] == 5

    def test_slug_is_rejected_as_unknown_field(self, client, db, auth_headers):
        """`slug` no está en el schema de update (es inmutable) → 422 explícito,
        no un cambio silencioso que dejaría menús huérfanos."""
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = client.put(
            f"/api/menu-services/{sid}",
            json={"slug": "otro", "name": "Nuevo"},
            headers=auth_headers(),
        )
        assert res.status_code == 422
        # El slug sigue intacto en la DB
        from bson import ObjectId
        assert db["menu_services"].find_one({"_id": ObjectId(sid)})["slug"] == "desayunos"

    def test_deactivating_warns_about_hidden_menus(self, client, db, auth_headers):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        seed_menu(db, service_slugs=["desayunos"])
        res = client.put(
            f"/api/menu-services/{sid}",
            json={"is_active": False},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        assert res.json["affected_menus"] == 1


@pytest.mark.e2e
class TestDeleteService:
    def test_deletes_when_not_referenced(self, client, db, auth_headers):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = client.delete(f"/api/menu-services/{sid}", headers=auth_headers())
        assert res.status_code == 200

    def test_blocked_with_409_when_referenced(self, client, db, auth_headers):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        seed_menu(db, service_slugs=["desayunos"])
        res = client.delete(f"/api/menu-services/{sid}", headers=auth_headers())
        assert res.status_code == 409


@pytest.mark.e2e
class TestPublicServices:
    def test_public_list_is_open(self, client, db):
        seed_menu_service(db, slug="desayunos", labels={"es-ES": "Desayunos"})
        res = client.get("/api/menu-services/public?locale=es-ES")
        assert res.status_code == 200
        item = res.json["items"][0]
        assert item["slug"] == "desayunos"
        assert item["label"] == "Desayunos"

    def test_public_list_excludes_inactive(self, client, db):
        seed_menu_service(db, slug="on", is_active=True)
        seed_menu_service(db, slug="off", is_active=False)
        res = client.get("/api/menu-services/public")
        slugs = [s["slug"] for s in res.json["items"]]
        assert slugs == ["on"]
