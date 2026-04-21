"""
Tests del sistema de permisos y autorización.

Valida el comportamiento de los decoradores en `aralar.core.security`:
- `require_permissions`: exige TODOS los permisos listados
- `require_any_permission`: exige AL MENOS UNO
- `require_roles` / `require_any_role`: idem con roles

Estrategia: usar `auth_headers(permissions=[...])` para generar tokens con
permisos específicos y hacer requests a endpoints protegidos para verificar
que aceptan/rechazan correctamente.

Endpoint útil para tests: cualquiera que use `@require_permissions(...)`.
Ejemplos: GET /api/menus (menus:read), POST /api/menus (menus:create).
"""
import pytest


@pytest.mark.e2e
class TestRequirePermissions:
    """
    TODO (junior):
    - test_allows_access_when_user_has_required_permission
    - test_denies_access_with_403_when_permission_missing
    - test_returns_401_when_no_token_provided
    - test_returns_401_when_token_is_malformed
    - test_denies_when_user_has_some_but_not_all_permissions
    """
    pass


@pytest.mark.e2e
class TestTokenVersion:
    """
    Tests de la validación `perm_v` (token se invalida cuando cambian permisos).

    TODO (junior):
    - test_rejects_token_when_perm_version_mismatch
    - test_accepts_token_when_perm_version_matches
    """
    pass


@pytest.mark.e2e
class TestTokenBlacklist:
    """
    TODO (junior):
    - test_rejects_blacklisted_token
    - test_accepts_token_with_jti_not_in_blacklist
    """
    pass


@pytest.mark.e2e
class TestInactiveUser:
    """
    TODO (junior):
    - test_rejects_token_when_user_is_deactivated
    - test_rejects_token_when_user_no_longer_exists
    """
    pass
