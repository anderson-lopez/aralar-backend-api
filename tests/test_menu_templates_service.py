"""
Tests de `aralar.services.menu_templates_service.MenuTemplatesService`.

Cubre la lógica de creación, publicación, versionado y consulta de templates.

Lee `aralar/services/menu_templates_service.py` antes de escribir tests.
Los templates son la base de los menús: definen qué secciones y campos tienen.

Patrón: seguir el mismo estilo que `test_menus_service.py` (unit + integration).
"""
import pytest

from aralar.services.menu_templates_service import MenuTemplatesService
from aralar.repositories.menu_templates_repo import MenuTemplatesRepo

from tests.factories import seed_template


@pytest.mark.integration
class TestCreateTemplate:
    """
    TODO (junior):
    - test_creates_template_with_status_draft
    - test_returns_400_when_slug_already_exists_in_same_tenant
    - test_accepts_multiple_locales_in_i18n_config
    """
    pass


@pytest.mark.integration
class TestPublishTemplate:
    """
    TODO (junior):
    - test_publishes_draft_template_successfully
    - test_increments_version_on_republish
    - test_creates_new_document_for_published_version (no mutate draft)
    - test_returns_error_when_template_already_published
    """
    pass


@pytest.mark.integration
class TestListTemplates:
    """
    TODO (junior):
    - test_lists_only_templates_of_current_tenant
    - test_filters_by_status
    - test_returns_latest_version_only_when_requested
    """
    pass


@pytest.mark.integration
class TestGetTemplateBySlugVersion:
    """
    TODO (junior):
    - test_returns_template_matching_slug_and_version
    - test_returns_none_when_not_found
    """
    pass
