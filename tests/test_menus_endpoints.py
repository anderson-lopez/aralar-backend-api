"""
Tests E2E de endpoints HTTP de menús.

Estos tests usan `client` (test_client de Flask) para hacer requests reales
contra los endpoints, atravesando toda la stack: blueprint → schema validation
→ service → repository → mongomock.

Cuándo usar E2E:
- Para validar que endpoints protegidos rechazan sin token (401).
- Para validar status codes y forma de la respuesta JSON.
- Para validar query params, request body, y errores de validación (400/422).

Cuándo NO usar E2E:
- Si puedes probar la lógica con un unit test del service, prefiérelo: son
  ~100x más rápidos y fallan con mensajes más específicos.
"""
import pytest

from tests.factories import seed_menu, seed_template, make_image


# =============================================================================
# Endpoints públicos (sin autenticación)
# =============================================================================
@pytest.mark.e2e
class TestPublicAvailable:
    """
    Tests de `GET /api/menus/public/available`.
    """

    def test_returns_empty_list_when_no_menus_seeded(self, client):
        res = client.get("/api/menus/public/available?locale=es-ES&date=2025-09-27")
        assert res.status_code == 200
        assert res.json == {"items": []}

    def test_returns_seeded_menu_with_expected_fields(self, client, db):
        seed_menu(
            db,
            name="Menú de prueba",
            availability={
                "timezone": "Europe/Madrid",
                "days_of_week": ["SAT"],
                "date_ranges": [{"start": "2025-09-01", "end": "2025-12-31"}],
            },
        )
        res = client.get("/api/menus/public/available?locale=es-ES&date=2025-09-27")

        assert res.status_code == 200
        items = res.json["items"]
        assert len(items) == 1
        expected_keys = {
            "id", "name", "template_slug", "template_version",
            "updated_at", "title", "summary", "preview_images",
        }
        assert set(items[0].keys()) == expected_keys
        assert items[0]["preview_images"] == []

    def test_returns_preview_images_when_menu_has_images(self, client, db):
        seed_menu(
            db,
            common={"header": {"banner_image": make_image(url="https://cdn/banner.webp")}},
            availability={
                "timezone": "Europe/Madrid",
                "days_of_week": ["SAT"],
                "date_ranges": [{"start": "2025-09-01", "end": "2025-12-31"}],
            },
        )
        res = client.get("/api/menus/public/available?locale=es-ES&date=2025-09-27")
        assert res.json["items"][0]["preview_images"] == ["https://cdn/banner.webp"]

    def test_returns_400_when_date_is_invalid(self, client):
        res = client.get("/api/menus/public/available?locale=es-ES&date=not-a-date")
        assert res.status_code == 400

    def test_requires_locale_query_param(self, client):
        res = client.get("/api/menus/public/available")
        # flask-smorest puede devolver 400 o 422 según versión
        assert res.status_code in (400, 422)

    def test_respects_images_limit_query_param(self, client, db):
        seed_menu(
            db,
            common={
                "dishes": [
                    {"_id": f"d{i}", "image": make_image(url=f"https://cdn/d{i}.webp")}
                    for i in range(8)
                ]
            },
        )
        res = client.get(
            "/api/menus/public/available?locale=es-ES&date=2025-09-27&images_limit=3"
        )
        assert len(res.json["items"][0]["preview_images"]) == 3

    def test_returns_empty_when_date_outside_availability_range(self, client, db):
        seed_menu(
            db,
            availability={
                "timezone": "Europe/Madrid",
                "days_of_week": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
                "date_ranges": [{"start": "2025-09-01", "end": "2025-09-30"}],
            },
        )
        res = client.get("/api/menus/public/available?locale=es-ES&date=2025-10-15")
        assert res.json["items"] == []


@pytest.mark.e2e
class TestPublicFeatured:
    """
    Tests de `GET /api/menus/public/featured`.
    """

    def test_returns_empty_list_when_no_featured_menus(self, client, db):
        seed_menu(db, name="No featured", featured=False)
        res = client.get("/api/menus/public/featured?locale=es-ES&date=2025-09-27")
        assert res.status_code == 200
        assert res.json["items"] == []

    def test_returns_only_featured_menus(self, client, db):
        seed_menu(db, name="Featured", featured=True, featured_order=1)
        seed_menu(db, name="Normal", featured=False)
        res = client.get("/api/menus/public/featured?locale=es-ES&date=2025-09-27")
        names = [m["name"] for m in res.json["items"]]
        assert names == ["Featured"]

    def test_respects_featured_order(self, client, db):
        seed_menu(db, name="Segundo", featured=True, featured_order=20)
        seed_menu(db, name="Primero", featured=True, featured_order=10)
        res = client.get("/api/menus/public/featured?locale=es-ES&date=2025-09-27")
        names = [m["name"] for m in res.json["items"]]
        assert names == ["Primero", "Segundo"]

    def test_includes_ui_manifest_when_include_ui_true(self, client, db):
        seed_template(db, slug="test-template", version=1)
        seed_menu(db, featured=True, featured_order=1)
        res = client.get(
            "/api/menus/public/featured?locale=es-ES&date=2025-09-27&include_ui=true"
        )
        assert "ui" in res.json["items"][0]


@pytest.mark.e2e
class TestRender:
    """
    Tests de `GET /api/menus/<id>/render`.
    """

    def test_returns_rendered_menu_for_requested_locale(self, client, db):
        menu = seed_menu(
            db,
            common={"items": [{"_id": "i1"}]},
            locales={"es-ES": {"data": {"items": [{"_id": "i1", "name": "Plato"}]},
                                "meta": {"title": "Mi menú"}}},
        )
        res = client.get(f"/api/menus/{menu['_id']}/render?locale=es-ES")
        assert res.status_code == 200
        assert res.json["locale"] == "es-ES"
        assert res.json["data"]["items"][0]["name"] == "Plato"

    def test_returns_400_when_locale_missing(self, client, db):
        menu = seed_menu(db)
        res = client.get(f"/api/menus/{menu['_id']}/render")
        # Bypassed schema validation = 422; abort en blueprint = 400.
        assert res.status_code in (400, 422)

    def test_returns_400_when_menu_id_is_invalid(self, client):
        res = client.get("/api/menus/no-es-objectid/render?locale=es-ES")
        assert res.status_code == 400

    def test_returns_404_when_menu_not_found(self, client):
        from bson import ObjectId
        res = client.get(f"/api/menus/{ObjectId()}/render?locale=es-ES")
        assert res.status_code == 404

    def test_returns_409_when_menu_not_published_in_locale(self, client, db):
        menu = seed_menu(db, publish={})
        res = client.get(f"/api/menus/{menu['_id']}/render?locale=es-ES")
        assert res.status_code == 409


# =============================================================================
# Endpoints protegidos (requieren JWT + permisos)
# =============================================================================
@pytest.mark.e2e
class TestCreateMenu:
    """
    Tests de `POST /api/menus`.
    Requiere permiso `menus:create`.
    """

    def test_returns_401_without_token(self, client):
        res = client.post("/api/menus", json={
            "tenant_id": "aralar", "name": "M", "common": {},
            "template_slug": "test-template", "template_version": 1,
        })
        assert res.status_code == 401

    def test_returns_403_without_menus_create_permission(self, client, auth_headers):
        res = client.post(
            "/api/menus",
            json={"tenant_id": "aralar", "name": "M", "common": {},
                  "template_slug": "test-template", "template_version": 1},
            headers=auth_headers(permissions=["menus:read"]),
        )
        assert res.status_code == 403

    def test_returns_400_when_template_does_not_exist(self, client, auth_headers):
        res = client.post(
            "/api/menus",
            json={"tenant_id": "aralar", "name": "M", "common": {},
                  "template_slug": "no-existe", "template_version": 1},
            headers=auth_headers(),
        )
        assert res.status_code == 400

    def test_creates_menu_and_returns_201(self, client, db, auth_headers):
        seed_template(db, slug="test-template", version=1)
        res = client.post(
            "/api/menus",
            json={"tenant_id": "aralar", "name": "Mi menú", "common": {},
                  "template_slug": "test-template", "template_version": 1},
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert res.json["name"] == "Mi menú"

    def test_persists_menu_in_database(self, client, db, auth_headers):
        seed_template(db, slug="test-template", version=1)
        client.post(
            "/api/menus",
            json={"tenant_id": "aralar", "name": "Persistido", "common": {},
                  "template_slug": "test-template", "template_version": 1},
            headers=auth_headers(),
        )
        assert db["menus"].count_documents({"name": "Persistido"}) == 1


@pytest.mark.e2e
class TestListMenus:
    """
    Tests de `GET /api/menus`.
    """

    def test_returns_401_without_token(self, client):
        res = client.get("/api/menus")
        assert res.status_code == 401

    def test_returns_paginated_list(self, client, db, auth_headers):
        seed_menu(db, name="A")
        seed_menu(db, name="B")
        res = client.get("/api/menus", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["total"] == 2
        assert len(res.json["items"]) == 2

    def test_respects_skip_and_limit_params(self, client, db, auth_headers):
        for i in range(5):
            seed_menu(db, name=f"M{i}")
        res = client.get("/api/menus?skip=2&limit=2", headers=auth_headers())
        assert res.json["total"] == 5
        assert len(res.json["items"]) == 2

    def test_filters_by_status(self, client, db, auth_headers):
        seed_menu(db, name="Draft", status="draft")
        seed_menu(db, name="Pub", status="published")
        res = client.get("/api/menus?status=draft", headers=auth_headers())
        names = [m["name"] for m in res.json["items"]]
        assert names == ["Draft"]


@pytest.mark.e2e
class TestGetMenu:
    """Tests de `GET /api/menus/<id>`."""

    def test_returns_401_without_token(self, client, db):
        menu = seed_menu(db)
        res = client.get(f"/api/menus/{menu['_id']}")
        assert res.status_code == 401

    def test_returns_menu_by_id(self, client, db, auth_headers):
        menu = seed_menu(db, name="Buscado")
        res = client.get(f"/api/menus/{menu['_id']}", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["name"] == "Buscado"

    def test_returns_404_when_menu_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.get(f"/api/menus/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404


@pytest.mark.e2e
class TestDeleteMenu:
    """Tests de `DELETE /api/menus/<id>`."""

    def test_returns_401_without_token(self, client, db):
        menu = seed_menu(db)
        res = client.delete(f"/api/menus/{menu['_id']}")
        assert res.status_code == 401

    def test_returns_404_when_menu_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.delete(f"/api/menus/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404

    def test_deletes_menu_when_exists(self, client, db, auth_headers):
        menu = seed_menu(db)
        res = client.delete(f"/api/menus/{menu['_id']}", headers=auth_headers())
        assert res.status_code == 200
        assert db["menus"].count_documents({}) == 0


@pytest.mark.e2e
class TestSetAvailability:
    """Tests de `PUT /api/menus/<id>/availability`."""

    def _payload(self):
        return {
            "timezone": "Europe/Madrid",
            "days_of_week": ["MON", "TUE"],
            "date_ranges": [{"start": "2025-01-01", "end": "2025-12-31"}],
        }

    def test_returns_401_without_token(self, client, db):
        menu = seed_menu(db)
        res = client.put(f"/api/menus/{menu['_id']}/availability", json=self._payload())
        assert res.status_code == 401

    def test_returns_404_when_menu_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.put(
            f"/api/menus/{ObjectId()}/availability",
            json=self._payload(),
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_updates_availability_successfully(self, client, db, auth_headers):
        menu = seed_menu(db)
        res = client.put(
            f"/api/menus/{menu['_id']}/availability",
            json=self._payload(),
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["availability"]["timezone"] == "Europe/Madrid"


@pytest.mark.e2e
class TestPublishMenu:
    """Tests de `POST /api/menus/<id>/publish/<locale>` y `/<id>/publish`."""

    def test_returns_404_when_menu_not_found_publish_locale(self, client, auth_headers):
        from bson import ObjectId
        res = client.post(
            f"/api/menus/{ObjectId()}/publish/es-ES",
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_publishes_locale_successfully(self, client, db, auth_headers):
        menu = seed_menu(db, publish={})
        res = client.post(
            f"/api/menus/{menu['_id']}/publish/es-ES",
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["publish"]["es-ES"]["status"] == "published"

    def test_publish_menu_returns_409_when_no_availability(self, client, db, auth_headers):
        menu = seed_menu(db, availability={}, publish={})
        res = client.post(f"/api/menus/{menu['_id']}/publish", headers=auth_headers())
        assert res.status_code == 409


@pytest.mark.e2e
class TestSetFeatured:
    """Tests de `PUT /api/menus/<id>/featured`."""

    def test_returns_404_when_menu_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.put(
            f"/api/menus/{ObjectId()}/featured",
            json={"featured": True, "featured_order": 1},
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_sets_menu_as_featured(self, client, db, auth_headers):
        menu = seed_menu(db, featured=False)
        res = client.put(
            f"/api/menus/{menu['_id']}/featured",
            json={"featured": True, "featured_order": 3},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["featured"] is True
        assert stored["featured_order"] == 3


@pytest.mark.e2e
class TestUpdateMenuCommon:
    """Tests de `PUT /api/menus/<id>/common`."""

    def test_returns_404_when_menu_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.put(
            f"/api/menus/{ObjectId()}/common",
            json={"common": {}},
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_updates_common_block(self, client, db, auth_headers):
        menu = seed_menu(db)
        res = client.put(
            f"/api/menus/{menu['_id']}/common",
            json={"common": {"x": "valor"}},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["common"]["x"] == "valor"


@pytest.mark.e2e
class TestUpdateMenuLocale:
    """Tests de `PUT /api/menus/<id>/locales/<locale>`."""

    def test_returns_404_when_menu_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.put(
            f"/api/menus/{ObjectId()}/locales/es-ES",
            json={"data": {}, "meta": {}},
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_updates_locale_data(self, client, db, auth_headers):
        menu = seed_menu(db)
        res = client.put(
            f"/api/menus/{menu['_id']}/locales/en-GB",
            json={"data": {"x": "EN value"}, "meta": {"title": "Title EN"}},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["locales"]["en-GB"]["data"]["x"] == "EN value"
