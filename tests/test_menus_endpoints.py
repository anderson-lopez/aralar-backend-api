"""
Tests E2E de endpoints HTTP de menús.

Estos tests usan `client` (test_client de Flask) para hacer requests reales
contra los endpoints, atravesando toda la stack: blueprint → schema validation
→ service → repository → mongomock.

Diferencia vs `test_menus_service.py`:
- Aquí testeamos el COMPORTAMIENTO HTTP completo (status codes, JSON, auth).
- Allá testeamos LÓGICA de los métodos del service aisladamente.

Cuándo usar E2E:
- Para validar que endpoints protegidos rechazan sin token (401).
- Para validar status codes y forma de la respuesta JSON.
- Para validar query params, request body, y errores de validación (400).

Cuándo NO usar E2E:
- Si puedes probar la lógica con un unit test del service, prefiérelo: son
  ~100x más rápidos y fallan con mensajes más específicos.
"""
import pytest

from tests.factories import seed_menu, seed_template


# =============================================================================
# Endpoints públicos (sin autenticación)
# =============================================================================
@pytest.mark.e2e
class TestPublicAvailable:
    """
    Tests de `GET /api/menus/public/available`.

    ✅ Este es un EJEMPLO COMPLETO funcionando. Úsalo como plantilla.
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
        # La respuesta debe incluir los 8 campos del schema
        expected_keys = {
            "id", "name", "template_slug", "template_version",
            "updated_at", "title", "summary", "preview_images",
        }
        assert set(items[0].keys()) == expected_keys
        assert items[0]["preview_images"] == []  # menu sin imágenes

    def test_returns_preview_images_when_menu_has_images(self, client, db):
        from tests.factories import make_image
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
        assert res.status_code in (400, 422)  # flask-smorest devuelve 422 en validation

    # TODO (junior): más casos sugeridos
    # - test_respects_images_limit_query_param
    # - test_returns_empty_when_date_outside_availability_range
    # - test_returns_empty_when_weekday_does_not_match
    # - test_falls_back_to_fallback_locale_for_meta


@pytest.mark.e2e
class TestPublicFeatured:
    """
    Tests de `GET /api/menus/public/featured`.

    TODO (junior):
    - test_returns_only_featured_menus
    - test_respects_featured_order
    - test_includes_ui_manifest_when_include_ui_true
    - test_returns_rendered_menu_with_data_section
    """
    pass


@pytest.mark.e2e
class TestRender:
    """
    Tests de `GET /api/menus/<id>/render`.

    TODO (junior):
    - test_returns_rendered_menu_for_requested_locale
    - test_returns_404_when_menu_not_found
    - test_returns_404_when_menu_not_published
    - test_uses_fallback_locale_when_primary_not_published
    """
    pass


# =============================================================================
# Endpoints protegidos (requieren JWT + permisos)
# =============================================================================
@pytest.mark.e2e
class TestCreateMenu:
    """
    Tests de `POST /api/menus`.

    TODO (junior): el endpoint requiere permiso `menus:create`.
    Usa `auth_headers()` para autenticar y `auth_headers(permissions=["other"])`
    para probar que rechaza con permisos insuficientes.

    Casos sugeridos:
    - test_returns_401_without_token
    - test_returns_403_when_user_lacks_menus_create_permission
    - test_creates_menu_and_returns_201_with_id
    - test_returns_400_when_template_does_not_exist
    - test_persists_menu_in_database
    """
    pass


@pytest.mark.e2e
class TestListMenus:
    """
    Tests de `GET /api/menus`.

    TODO (junior):
    - test_returns_401_without_token
    - test_returns_paginated_list
    - test_respects_skip_and_limit_params
    - test_filters_by_status
    """
    pass


@pytest.mark.e2e
class TestSetAvailability:
    """
    Tests de `PUT /api/menus/<id>/availability`.

    TODO (junior):
    - test_updates_availability_successfully
    - test_returns_400_when_invalid_days_of_week
    - test_returns_404_when_menu_not_found
    """
    pass


@pytest.mark.e2e
class TestPublishMenu:
    """
    Tests de `POST /api/menus/<id>/publish/<locale>`.

    TODO (junior): el publish requiere que el menú tenga availability configurada
    y al menos un locale con data. Revisa `menus_service.py:publish_locale` para
    los casos de error (422 sin availability, 422 sin data, etc.).
    """
    pass
