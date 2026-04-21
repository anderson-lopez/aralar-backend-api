"""
Tests E2E del flujo de autenticación.

Endpoints bajo `/api/auth/...`: login, refresh, logout.

⚠️ OJO: estos tests NO usan `auth_headers` (esa fixture genera tokens
directamente). Aquí probamos el endpoint que GENERA los tokens, así que
necesitas crear un usuario en la DB con password hasheado de verdad y
hacer el request de login real.

Helper para hashear password (argon2-cffi ya está en requirements):
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    hashed = ph.hash("mi-password")
"""
import pytest


@pytest.mark.e2e
class TestLogin:
    """
    POST /api/auth/login

    TODO (junior):
    - test_returns_access_token_on_valid_credentials
    - test_returns_refresh_token_on_valid_credentials
    - test_returns_401_on_invalid_password
    - test_returns_401_on_non_existent_email
    - test_returns_401_when_user_is_inactive
    - test_response_contains_user_info (email, roles, permissions)
    """
    pass


@pytest.mark.e2e
class TestRefresh:
    """
    POST /api/auth/refresh

    TODO (junior):
    - test_returns_new_access_token_with_valid_refresh_token
    - test_returns_401_with_invalid_refresh_token
    - test_returns_401_when_refresh_token_is_expired
    """
    pass


@pytest.mark.e2e
class TestLogout:
    """
    POST /api/auth/logout

    TODO (junior): este endpoint añade el JTI del token a la blacklist.
    Después del logout, el mismo token debería ser rechazado (ver
    `test_permissions.py` y el _validate_token_blacklist de security.py).

    - test_blacklists_token_on_logout
    - test_token_is_rejected_after_logout
    - test_returns_401_without_token
    """
    pass
