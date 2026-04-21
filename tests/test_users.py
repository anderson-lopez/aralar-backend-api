"""
Tests E2E de endpoints de usuarios.

Endpoints bajo `/api/users/...`: CRUD de usuarios y gestión de permisos.

Referencias:
- Blueprint: `aralar/api/users/blueprint.py`
- Service: `aralar/services/users_service.py`
- Repo: `aralar/repositories/users_repo.py`
"""
import pytest


@pytest.mark.e2e
class TestCreateUser:
    """
    POST /api/users

    TODO (junior):
    - test_returns_401_without_token
    - test_returns_403_without_users_create_permission
    - test_creates_user_and_returns_201
    - test_returns_400_when_email_already_exists
    - test_returns_400_when_email_invalid
    - test_hashes_password_before_storing (verifica que no se guarda en plano)
    """
    pass


@pytest.mark.e2e
class TestListUsers:
    """
    GET /api/users

    TODO (junior):
    - test_returns_paginated_users_list
    - test_does_not_expose_password_hash_in_response
    - test_filters_by_active_status
    """
    pass


@pytest.mark.e2e
class TestGetUser:
    """
    GET /api/users/<id>

    TODO (junior):
    - test_returns_user_by_id
    - test_returns_404_when_user_not_found
    """
    pass


@pytest.mark.e2e
class TestUpdateUser:
    """
    PUT /api/users/<id>

    TODO (junior):
    - test_updates_fullname_successfully
    - test_updates_active_flag
    - test_rejects_email_change_to_existing_email
    """
    pass


@pytest.mark.e2e
class TestUpdateUserPermissions:
    """
    Endpoint(s) que cambian permisos/roles del usuario. Cuando cambia,
    `perm_version` debe incrementarse para invalidar tokens viejos.

    TODO (junior):
    - test_increments_perm_version_when_roles_change
    - test_increments_perm_version_when_permissions_change
    """
    pass
