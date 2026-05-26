"""
Tests E2E de endpoints de usuarios.

Endpoints bajo `/api/users/...`: CRUD de usuarios, gestión de permisos y roles.

Referencias:
- Blueprint: `aralar/api/users/blueprint.py`
- Service: `aralar/services/users_service.py`
"""
import pytest

from argon2 import PasswordHasher

ph = PasswordHasher()


def _valid_create_payload(email="new@test.com", password="ValidPass123"):
    """Payload completo que cumple validate_password_strength + email format."""
    return {
        "email": email,
        "password": password,
        "confirm_password": password,
        "full_name": "Nuevo Usuario",
        "roles": ["admin"],
        "permissions_allow": [],
        "permissions_deny": [],
    }


@pytest.mark.e2e
class TestCreateUser:
    """POST /api/users"""

    def test_returns_401_without_token(self, client):
        res = client.post("/api/users", json=_valid_create_payload())
        assert res.status_code == 401

    def test_returns_403_without_users_create_permission(self, client, auth_headers):
        res = client.post(
            "/api/users",
            json=_valid_create_payload(),
            headers=auth_headers(permissions=["users:read"]),
        )
        assert res.status_code == 403

    def test_creates_user_and_returns_201(self, client, auth_headers):
        res = client.post(
            "/api/users",
            json=_valid_create_payload(email="newcreated@test.com"),
            headers=auth_headers(),
        )
        assert res.status_code == 201
        assert "id" in res.json

    def test_returns_409_when_email_already_exists(self, client, db, auth_headers):
        db["users"].insert_one({"email": "exists@test.com", "password_hash": "x"})
        res = client.post(
            "/api/users",
            json=_valid_create_payload(email="exists@test.com"),
            headers=auth_headers(),
        )
        assert res.status_code == 409

    def test_returns_422_when_password_too_weak(self, client, auth_headers):
        payload = _valid_create_payload(password="weak")  # < 8 chars
        payload["confirm_password"] = "weak"
        res = client.post("/api/users", json=payload, headers=auth_headers())
        assert res.status_code == 422

    def test_hashes_password_before_storing(self, client, db, auth_headers):
        client.post(
            "/api/users",
            json=_valid_create_payload(email="hashed@test.com", password="Strong1234"),
            headers=auth_headers(),
        )
        stored = db["users"].find_one({"email": "hashed@test.com"})
        # El password NO se guarda en plano.
        assert "Strong1234" not in str(stored.get("password_hash", ""))
        # Pero el hash sí se puede verificar.
        ph.verify(stored["password_hash"], "Strong1234")


@pytest.mark.e2e
class TestListUsers:
    """GET /api/users"""

    def test_returns_401_without_token(self, client):
        res = client.get("/api/users")
        assert res.status_code == 401

    def test_returns_paginated_users_list(self, client, db, auth_headers):
        # auth_headers inserta el user "test@aralar.local" automáticamente.
        db["users"].insert_one({"email": "extra@test.com", "full_name": "Extra"})
        res = client.get("/api/users", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["total"] >= 2

    def test_does_not_expose_password_hash_in_response(self, client, db, auth_headers):
        db["users"].insert_one({
            "email": "sensitive@test.com",
            "full_name": "S",
            "password_hash": "argon2$mysecret",
        })
        res = client.get("/api/users", headers=auth_headers())
        # Ningún item debe traer password_hash en el JSON serializado.
        for item in res.json["items"]:
            assert "password_hash" not in item


@pytest.mark.e2e
class TestGetUser:
    """GET /api/users/<id>"""

    def test_returns_404_when_user_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.get(f"/api/users/{ObjectId()}", headers=auth_headers())
        assert res.status_code == 404

    def test_returns_user_by_id(self, client, db, auth_headers):
        _id = db["users"].insert_one({
            "email": "findme@test.com", "full_name": "Find Me",
            "roles": ["admin"], "is_active": True,
        }).inserted_id
        res = client.get(f"/api/users/{_id}", headers=auth_headers())
        assert res.status_code == 200
        assert res.json["email"] == "findme@test.com"


@pytest.mark.e2e
class TestUpdateUser:
    """PUT /api/users/<id>"""

    def test_returns_404_when_user_not_found(self, client, auth_headers):
        from bson import ObjectId
        res = client.put(
            f"/api/users/{ObjectId()}",
            json={"full_name": "x"},
            headers=auth_headers(),
        )
        assert res.status_code == 404

    def test_updates_full_name_successfully(self, client, db, auth_headers):
        _id = db["users"].insert_one({
            "email": "tochange@test.com", "full_name": "Old", "is_active": True,
        }).inserted_id
        res = client.put(
            f"/api/users/{_id}",
            json={"full_name": "New Name"},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["users"].find_one({"_id": _id})
        assert stored["full_name"] == "New Name"


@pytest.mark.e2e
class TestUpdateUserRoles:
    """PUT /api/users/<id>/roles"""

    def test_increments_perm_version_when_roles_change(self, client, db, auth_headers):
        _id = db["users"].insert_one({
            "email": "roles@test.com", "full_name": "R",
            "roles": ["admin"], "is_active": True, "perm_version": 1,
        }).inserted_id
        res = client.put(
            f"/api/users/{_id}/roles",
            json={"roles": ["admin", "editor"]},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["users"].find_one({"_id": _id})
        assert stored["perm_version"] == 2  # incrementó


@pytest.mark.e2e
class TestUpdateUserPermissions:
    """PUT /api/users/<id>/permissions"""

    def test_increments_perm_version_when_permissions_change(self, client, db, auth_headers):
        _id = db["users"].insert_one({
            "email": "perms@test.com", "full_name": "P",
            "roles": [], "permissions_allow": [], "permissions_deny": [],
            "is_active": True, "perm_version": 1,
        }).inserted_id
        res = client.put(
            f"/api/users/{_id}/permissions",
            json={"permissions_allow": ["menus:read"], "permissions_deny": []},
            headers=auth_headers(),
        )
        assert res.status_code == 200
        stored = db["users"].find_one({"_id": _id})
        assert stored["permissions_allow"] == ["menus:read"]
        assert stored["perm_version"] == 2


@pytest.mark.e2e
class TestDeleteUserSelfLock:
    """
    Test del guard anti-softlock: el usuario logeado no puede eliminarse
    a sí mismo, ni eliminar al último admin activo.
    """

    def test_prevents_user_from_deleting_themselves(self, client, db, auth_headers):
        headers = auth_headers(email="cantdelete@test.com")
        user = db["users"].find_one({"email": "cantdelete@test.com"})
        res = client.delete(f"/api/users/{user['_id']}", headers=headers)
        assert res.status_code == 400

    def test_prevents_deactivating_self(self, client, db, auth_headers):
        headers = auth_headers(email="cantdeactivate@test.com")
        user = db["users"].find_one({"email": "cantdeactivate@test.com"})
        res = client.put(
            f"/api/users/{user['_id']}/deactivate",
            headers=headers,
        )
        assert res.status_code == 400


@pytest.mark.e2e
class TestActivateDeactivate:
    """PUT /api/users/<id>/activate y /deactivate"""

    def test_activates_user(self, client, db, auth_headers):
        _id = db["users"].insert_one({
            "email": "toactivate@test.com", "full_name": "A",
            "is_active": False, "roles": [],
        }).inserted_id
        res = client.put(f"/api/users/{_id}/activate", headers=auth_headers())
        assert res.status_code == 200
        stored = db["users"].find_one({"_id": _id})
        assert stored["is_active"] is True

    def test_deactivates_user(self, client, db, auth_headers):
        _id = db["users"].insert_one({
            "email": "todeactivate@test.com", "full_name": "D",
            "is_active": True, "roles": [],
        }).inserted_id
        res = client.put(f"/api/users/{_id}/deactivate", headers=auth_headers())
        assert res.status_code == 200
        stored = db["users"].find_one({"_id": _id})
        assert stored["is_active"] is False
