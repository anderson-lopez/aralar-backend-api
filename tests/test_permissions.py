"""
Tests del sistema de permisos y autorización.

Valida el comportamiento de los decoradores en `aralar.core.security`:
- `require_permissions`: exige TODOS los permisos listados.
- `_validate_token_version`: rechaza si `perm_v` no coincide con la DB.
- `_validate_token_blacklist`: rechaza si el JTI está en la blacklist.
- `_validate_token_version`: rechaza si el usuario está desactivado o no existe.

Usamos `/api/menus` (requiere `menus:read`) como endpoint protegido de prueba.
"""
from datetime import datetime, timedelta, timezone

import pytest


@pytest.mark.e2e
class TestRequirePermissions:
    """
    Tests del decorador `require_permissions`.
    """

    def test_returns_401_when_no_token_provided(self, client):
        res = client.get("/api/menus")
        assert res.status_code == 401

    def test_rejects_request_when_token_is_malformed(self, client):
        # flask-jwt-extended devuelve 422 ante tokens malformados (sintaxis
        # JWT inválida) y 401 cuando falta o expira; ambos son rechazos
        # válidos. Aceptamos cualquiera de los dos.
        res = client.get("/api/menus", headers={"Authorization": "Bearer not-a-jwt"})
        assert res.status_code in (401, 422)

    def test_allows_access_when_user_has_required_permission(self, client, auth_headers):
        res = client.get("/api/menus", headers=auth_headers(permissions=["menus:read"]))
        assert res.status_code == 200

    def test_denies_access_with_403_when_permission_missing(self, client, auth_headers):
        # Tiene un permiso, pero no el requerido `menus:read`.
        res = client.get("/api/menus", headers=auth_headers(permissions=["other:perm"]))
        assert res.status_code == 403

    def test_denies_when_user_has_some_but_not_all_required_permissions(
        self, client, auth_headers
    ):
        """
        El endpoint POST /api/menus requiere `menus:create`. Si el usuario
        solo tiene `menus:read`, debe ser rechazado.
        """
        res = client.post(
            "/api/menus",
            json={"tenant_id": "aralar", "name": "X", "common": {},
                  "template_slug": "test-template", "template_version": 1},
            headers=auth_headers(permissions=["menus:read"]),
        )
        assert res.status_code == 403


@pytest.mark.e2e
class TestTokenVersion:
    """
    Tests de la validación `perm_v` (token se invalida cuando cambian permisos
    del usuario en la BD).
    """

    def test_accepts_token_when_perm_version_matches(self, client, auth_headers):
        """auth_headers crea user con perm_version=1 y emite token con perm_v=1."""
        res = client.get("/api/menus", headers=auth_headers())
        assert res.status_code == 200

    def test_rejects_token_when_perm_version_mismatch(self, client, db, auth_headers):
        # Token emitido con perm_v=1.
        headers = auth_headers(email="bumped@test.com")
        # Bumpear la versión en la DB → ahora la BD tiene perm_version=2.
        db["users"].update_one({"email": "bumped@test.com"}, {"$set": {"perm_version": 2}})
        res = client.get("/api/menus", headers=headers)
        assert res.status_code == 401


@pytest.mark.e2e
class TestTokenBlacklist:
    """
    Tests de la blacklist de tokens (logout invalida).
    """

    def test_accepts_token_with_jti_not_in_blacklist(self, client, auth_headers):
        res = client.get("/api/menus", headers=auth_headers())
        assert res.status_code == 200

    def test_rejects_blacklisted_token(self, client, db, app, auth_headers):
        """Insertamos el JTI del token directamente en la blacklist."""
        from flask_jwt_extended import decode_token

        headers = auth_headers(email="blocked@test.com")
        token = headers["Authorization"].split(" ", 1)[1]
        with app.app_context():
            decoded = decode_token(token)
        jti = decoded.get("jti")
        # Cuando auth_headers no inyecta jti, no podemos blacklistear. Si no
        # hay jti, el guard permite pasar — el test se vuelve trivial. Para
        # que sea representativo, garantizamos un jti.
        if not jti:
            pytest.skip("auth_headers token without jti — blacklist test n/a")

        db["token_blacklist"].insert_one({
            "jti": jti,
            "user_id": "x",
            "blacklisted_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
            "reason": "logout",
        })

        res = client.get("/api/menus", headers=headers)
        assert res.status_code == 401


@pytest.mark.e2e
class TestInactiveUser:
    """
    Tests del guard que rechaza tokens cuando el user fue desactivado o eliminado.
    """

    def test_rejects_token_when_user_is_deactivated(self, client, db, auth_headers):
        headers = auth_headers(email="will-deactivate@test.com")
        db["users"].update_one(
            {"email": "will-deactivate@test.com"},
            {"$set": {"active": False}},
        )
        res = client.get("/api/menus", headers=headers)
        assert res.status_code == 401

    def test_rejects_token_when_user_no_longer_exists(self, client, db, auth_headers):
        headers = auth_headers(email="to-delete@test.com")
        db["users"].delete_one({"email": "to-delete@test.com"})
        res = client.get("/api/menus", headers=headers)
        assert res.status_code == 401
