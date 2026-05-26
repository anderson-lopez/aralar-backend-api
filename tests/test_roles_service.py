"""
Tests del `aralar.services.roles_service.RolesService`.

Cubre CRUD básico de roles y catálogo de permisos. Necesario para subir la
cobertura agregada de `aralar/services/` por encima del 70%.
"""
import pytest

from aralar.services.roles_service import RolesService
from aralar.repositories.roles_repo import RolesRepo


def _svc(db):
    return RolesService(RolesRepo(db))


@pytest.mark.integration
class TestRoles:
    """CRUD de roles."""

    def test_list_roles_returns_paginated_structure(self, db):
        # Sembramos dos roles.
        db["roles"].insert_many([
            {"name": "admin", "permissions": ["menus:read"]},
            {"name": "editor", "permissions": []},
        ])
        result = _svc(db).list_roles()
        assert set(result.keys()) == {"items", "total", "skip", "limit"}
        assert result["total"] == 2

    def test_get_role_returns_role_by_name(self, db):
        db["roles"].insert_one({"name": "viewer", "permissions": []})
        assert _svc(db).get_role("viewer")["name"] == "viewer"

    def test_get_role_returns_none_when_not_found(self, db):
        assert _svc(db).get_role("ghost") is None

    def test_create_role_raises_when_name_missing(self, db):
        with pytest.raises(ValueError):
            _svc(db).create_role({})

    def test_create_role_returns_conflict_when_already_exists(self, db):
        db["roles"].insert_one({"name": "dup", "permissions": []})
        result = _svc(db).create_role({"name": "dup"})
        assert isinstance(result, dict)
        assert "conflict" in result

    def test_create_role_persists_and_returns_doc(self, db):
        result = _svc(db).create_role({"name": "new_role", "permissions": ["menus:read"]})
        assert result["name"] == "new_role"
        assert "menus:read" in result["permissions"]

    def test_update_role_returns_none_when_role_not_found(self, db):
        assert _svc(db).update_role("ghost", {"permissions": []}) is None

    def test_update_role_replaces_permissions(self, db):
        db["roles"].insert_one({"name": "updatable", "permissions": ["menus:read"]})
        result = _svc(db).update_role("updatable", {"permissions": ["menus:create"]})
        assert "menus:create" in result["permissions"]
        assert "menus:read" not in result["permissions"]

    def test_delete_role_returns_deleted_count(self, db):
        db["roles"].insert_one({"name": "to_delete"})
        assert _svc(db).delete_role("to_delete") == 1

    def test_delete_role_returns_zero_when_not_found(self, db):
        assert _svc(db).delete_role("ghost") == 0


@pytest.mark.integration
class TestPermissions:
    """Catálogo de permisos (lista pura, no asignación)."""

    def test_list_permissions_returns_paginated_structure(self, db):
        db["permissions"].insert_many([
            {"name": "menus:read", "description": "Read menus"},
            {"name": "menus:create", "description": "Create menus"},
        ])
        result = _svc(db).list_permissions()
        assert result["total"] == 2

    def test_upsert_permission_creates_new(self, db):
        result = _svc(db).upsert_permission("notifications:read", {"description": "Read notifs"})
        assert result["name"] == "notifications:read"
        assert db["permissions"].count_documents({"name": "notifications:read"}) == 1

    def test_upsert_permission_updates_existing_description(self, db):
        db["permissions"].insert_one({"name": "existing", "description": "Old"})
        _svc(db).upsert_permission("existing", {"description": "New description"})
        stored = db["permissions"].find_one({"name": "existing"})
        assert stored["description"] == "New description"

    def test_update_permission_by_id_returns_none_when_invalid_id(self, db):
        result = _svc(db).update_permission_by_id("not-a-valid-objectid", {"description": "x"})
        assert result is None
