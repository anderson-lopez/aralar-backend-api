"""
Tests E2E de `aralar.api.menu_templates.blueprint`.

Endpoints sobre `/api/menu-templates/...` — CRUD de templates + publicación.

Todos requieren autenticación. Los permisos usados en el blueprint son
`menu_templates:*` (con underscore — el conftest los incluye en DEFAULT_PERMISSIONS).
"""
import pytest

from tests.factories import make_template, seed_template, seed_menu


@pytest.mark.e2e
class TestCreateTemplate:
    """POST /api/menu-templates"""

    def _payload(self, slug="nuevo", version=1):
        return {
            "tenant_id": "aralar",
            "name": "Mi template",
            "slug": slug,
            "version": version,
            "status": "draft",
            "i18n": {"default_locale": "es-ES", "locales": ["es-ES"]},
            "sections": [{
                "key": "items", "label": {"es-ES": "Items"}, "repeatable": True,
                "fields": [{"key": "_id", "type": "text", "required": True, "translatable": False}],
                "ui": {"role": "course_list", "order": 10, "display": "list"},
            }],
            "ui": {"layout": "sections", "catalogs": {}},
        }

    def test_returns_401_without_token(self, client):
        res = client.post("/api/menu-templates", json=self._payload())
        assert res.status_code == 401

    def test_returns_403_without_menu_templates_create_permission(self, client, auth_headers):
        res = client.post(
            "/api/menu-templates",
            json=self._payload(),
            headers=auth_headers(permissions=["menus:read"]),
        )
        assert res.status_code == 403

    def test_creates_template_and_returns_201(self, client, auth_headers):
        res = client.post(
            "/api/menu-templates",
            json=self._payload(slug="unico"),
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert "id" in res.json

    def test_returns_409_when_slug_version_duplicate(self, client, db, auth_headers):
        seed_template(db, slug="dup", version=1)
        res = client.post(
            "/api/menu-templates",
            json=self._payload(slug="dup", version=1),
            headers=auth_headers(),
        )
        assert res.status_code == 409


@pytest.mark.e2e
class TestListTemplates:
    """GET /api/menu-templates"""

    def test_returns_401_without_token(self, client):
        res = client.get("/api/menu-templates")
        assert res.status_code == 401

    def test_returns_paginated_list(self, client, db, auth_headers):
        seed_template(db, slug="a", version=1)
        seed_template(db, slug="b", version=1)
        res = client.get("/api/menu-templates", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["total"] == 2

    def test_filters_by_status(self, client, db, auth_headers):
        seed_template(db, slug="d", version=1, status="draft")
        seed_template(db, slug="p", version=1, status="published")
        res = client.get("/api/menu-templates?status=draft", headers=auth_headers())
        slugs = [t["slug"] for t in res.json["items"]]
        assert slugs == ["d"]


@pytest.mark.e2e
class TestGetTemplate:
    """GET /api/menu-templates/<id>"""

    def test_returns_401_without_token(self, client, db):
        tmpl = seed_template(db)
        res = client.get(f"/api/menu-templates/{tmpl['_id']}")
        assert res.status_code == 401

    def test_returns_template_by_id(self, client, db, auth_headers):
        tmpl = seed_template(db, slug="findme")
        res = client.get(f"/api/menu-templates/{tmpl['_id']}", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["slug"] == "findme"

    def test_returns_404_when_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.get(f"/api/menu-templates/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404


@pytest.mark.e2e
class TestPublishTemplate:
    """POST /api/menu-templates/<id>/publish"""

    def test_returns_404_when_template_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.post(
            f"/api/menu-templates/{ObjectId()}/publish",
            json={"notes": "first publish"},
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_publishes_draft_and_returns_201_with_id(self, client, db, auth_headers):
        tmpl = seed_template(db, slug="pub-me", status="draft")
        res = client.post(
            f"/api/menu-templates/{tmpl['_id']}/publish",
            json={"notes": "first"},
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert "id" in res.json


@pytest.mark.e2e
class TestUpdateTemplate:
    """
    PUT /api/menu-templates/<id>

    El schema de update extiende al de create y exige el payload completo
    (name, slug, tenant_id, sections...). Replicamos esa estructura aquí.
    """

    def _full_payload(self, name="Renombrado"):
        return {
            "tenant_id": "aralar",
            "name": name,
            "slug": "any-slug",
            "version": 1,
            "status": "draft",
            "i18n": {"default_locale": "es-ES", "locales": ["es-ES"]},
            "sections": [{
                "key": "items", "label": {"es-ES": "Items"}, "repeatable": True,
                "fields": [{"key": "_id", "type": "text", "required": True, "translatable": False}],
                "ui": {"role": "course_list", "order": 10, "display": "list"},
            }],
            "ui": {"layout": "sections", "catalogs": {}},
        }

    def test_returns_404_when_template_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.put(
            f"/api/menu-templates/{ObjectId()}",
            json=self._full_payload(),
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_returns_409_when_template_is_published(self, client, db, auth_headers):
        tmpl = seed_template(db, status="published")
        res = client.put(
            f"/api/menu-templates/{tmpl['_id']}",
            json=self._full_payload(),
            headers=auth_headers(),
        )
        assert res.status_code == 409

    def test_updates_draft_template_successfully(self, client, db, auth_headers):
        tmpl = seed_template(db, status="draft", name="Original")
        res = client.put(
            f"/api/menu-templates/{tmpl['_id']}",
            json=self._full_payload(name="Cambiado"),
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menu_templates"].find_one({"_id": tmpl["_id"]})
        assert stored["name"] == "Cambiado"


@pytest.mark.e2e
class TestDeleteTemplate:
    """DELETE /api/menu-templates/<id>"""

    def test_returns_404_when_template_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.delete(f"/api/menu-templates/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404

    def test_returns_409_when_menus_use_template(self, client, db, auth_headers):
        tmpl = seed_template(db, slug="usado", version=1)
        seed_menu(db, template_slug="usado", template_version=1)
        res = client.delete(
            f"/api/menu-templates/{tmpl['_id']}",
            headers=auth_headers(),
        )
        assert res.status_code == 409

    def test_deletes_template_when_no_menus_use_it(self, client, db, auth_headers):
        tmpl = seed_template(db, slug="huerfano", version=1)
        res = client.delete(
            f"/api/menu-templates/{tmpl['_id']}",
            headers=auth_headers(),
        )
        assert res.status_code == 200
        assert db["menu_templates"].count_documents({"slug": "huerfano"}) == 0


@pytest.mark.e2e
class TestUnpublishTemplate:
    """POST /api/menu-templates/<id>/unpublish"""

    def test_returns_404_when_template_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.post(
            f"/api/menu-templates/{ObjectId()}/unpublish",
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_returns_409_when_already_draft(self, client, db, auth_headers):
        tmpl = seed_template(db, status="draft")
        res = client.post(
            f"/api/menu-templates/{tmpl['_id']}/unpublish",
            headers=auth_headers(),
        )
        assert res.status_code == 409

    def test_unpublishes_template_successfully(self, client, db, auth_headers):
        tmpl = seed_template(db, status="published")
        res = client.post(
            f"/api/menu-templates/{tmpl['_id']}/unpublish",
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menu_templates"].find_one({"_id": tmpl["_id"]})
        assert stored["status"] == "draft"


@pytest.mark.e2e
class TestArchiveTemplate:
    """POST /api/menu-templates/<id>/archive"""

    def test_returns_404_when_template_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.post(
            f"/api/menu-templates/{ObjectId()}/archive",
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_archives_published_template(self, client, db, auth_headers):
        tmpl = seed_template(db, status="published")
        res = client.post(
            f"/api/menu-templates/{tmpl['_id']}/archive",
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["menu_templates"].find_one({"_id": tmpl["_id"]})
        assert stored["status"] == "archived"
