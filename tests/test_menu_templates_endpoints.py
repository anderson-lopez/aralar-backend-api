"""
Tests E2E de `aralar.api.menu_templates.blueprint`.

Endpoints sobre `/api/menu-templates/...` — CRUD de templates + publicación.

Todos requieren autenticación. Usa `auth_headers()` para simular un usuario
con permisos. Revisa los decoradores `@require_permissions(...)` en el
blueprint para saber qué permiso exige cada endpoint.
"""
import pytest


@pytest.mark.e2e
class TestCreateTemplate:
    """
    POST /api/menu-templates

    TODO (junior):
    - test_returns_401_without_token
    - test_returns_403_without_menu_templates_create_permission
    - test_creates_template_and_returns_201
    - test_returns_400_when_slug_duplicate
    - test_validates_sections_structure
    """
    pass


@pytest.mark.e2e
class TestPublishTemplate:
    """
    POST /api/menu-templates/<id>/publish

    TODO (junior):
    - test_publishes_draft_and_returns_201_with_new_id
    - test_returns_404_when_template_not_found
    - test_returns_error_when_template_already_published
    """
    pass


@pytest.mark.e2e
class TestListTemplates:
    """
    GET /api/menu-templates

    TODO (junior):
    - test_returns_401_without_token
    - test_returns_paginated_list
    - test_filters_by_status_param
    """
    pass


@pytest.mark.e2e
class TestGetTemplate:
    """
    GET /api/menu-templates/<id>

    TODO (junior):
    - test_returns_template_by_id
    - test_returns_404_when_not_found
    """
    pass
