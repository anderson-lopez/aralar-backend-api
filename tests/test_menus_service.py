"""
Tests de `aralar.services.menus_service.MenusService`.

Este archivo combina DOS tipos de tests:

1. UNIT tests (clase `TestExtractImageUrls` al inicio)
   → No tocan Mongo ni Flask. Construyen dicts en memoria y verifican la
     salida pura de un método. Son los más rápidos y los que más deberías
     escribir para lógica de negocio determinística.

2. INTEGRATION tests (clases `TestAvailableOn`, `TestResolveMeta`, ...)
   → Usan las fixtures `db` y las factories para sembrar datos en mongomock
     y verificar que el service + repo funcionan juntos correctamente.

Patrón recomendado para agregar nuevos tests:
- Agrupa por método en una `class TestNombreDelMetodo:`.
- Un test = un escenario. Nombre: `test_<metodo>_<escenario>_<resultado>`.
- Usa `@pytest.mark.parametrize` cuando varios casos comparten lógica y solo
  cambian los inputs/outputs.
- Usa `make_menu`, `make_image`, `seed_menu` de `tests.factories` en vez de
  escribir dicts gigantes inline.
"""
import pytest

from aralar.services.menus_service import MenusService
from aralar.repositories.menus_repo import MenusRepo
from aralar.repositories.menu_templates_repo import MenuTemplatesRepo

from tests.factories import make_menu, make_image, seed_menu


# =============================================================================
# UNIT TESTS — no tocan Mongo ni Flask
# =============================================================================
@pytest.mark.unit
class TestExtractImageUrls:
    """
    Tests del método `extract_image_urls(menu_doc, limit)`.

    Este método recorre `common` recursivamente y devuelve URLs de imagen
    (dicts con clave `url` string, opcionalmente filtrados por `mime`).

    ✅ Este es un EJEMPLO COMPLETO funcionando. Úsalo como plantilla para
    otros tests unitarios puros en este archivo.
    """

    def setup_method(self):
        """Se ejecuta antes de cada test de la clase. El service no necesita
        repos reales porque `extract_image_urls` no los usa."""
        self.svc = MenusService(repo=None, templates_repo=None)

    def test_returns_empty_list_when_menu_has_no_images(self):
        menu = make_menu(common={})
        assert self.svc.extract_image_urls(menu) == []

    def test_collects_single_image_from_banner(self):
        menu = make_menu(common={
            "header": {"banner_image": make_image(url="https://cdn/banner.webp")}
        })
        assert self.svc.extract_image_urls(menu) == ["https://cdn/banner.webp"]

    def test_collects_multiple_images_from_list(self):
        menu = make_menu(common={
            "dishes": [
                {"_id": "d1", "image": make_image(url="https://cdn/d1.webp")},
                {"_id": "d2", "image": make_image(url="https://cdn/d2.webp")},
            ]
        })
        assert self.svc.extract_image_urls(menu) == [
            "https://cdn/d1.webp",
            "https://cdn/d2.webp",
        ]

    def test_collects_images_from_nested_array_field(self):
        """Caso `images: [img1, img2]` dentro de cada item (template three-sections)."""
        menu = make_menu(common={
            "starters": [
                {"_id": "s1", "images": [
                    make_image(url="https://cdn/s1-1.webp"),
                    make_image(url="https://cdn/s1-2.webp"),
                ]},
            ]
        })
        assert self.svc.extract_image_urls(menu) == [
            "https://cdn/s1-1.webp",
            "https://cdn/s1-2.webp",
        ]

    def test_deduplicates_repeated_urls(self):
        menu = make_menu(common={
            "a": {"image": make_image(url="https://cdn/same.webp")},
            "b": {"image": make_image(url="https://cdn/same.webp")},
        })
        assert self.svc.extract_image_urls(menu) == ["https://cdn/same.webp"]

    def test_ignores_dict_with_non_image_mime(self):
        """Si un dict tiene `url` pero `mime` no empieza por `image/`, se descarta."""
        menu = make_menu(common={
            "doc": {"url": "https://cdn/manual.pdf", "mime": "application/pdf"},
            "photo": make_image(url="https://cdn/photo.webp"),
        })
        assert self.svc.extract_image_urls(menu) == ["https://cdn/photo.webp"]

    @pytest.mark.parametrize("limit,expected_count", [(1, 1), (2, 2), (10, 3)])
    def test_respects_limit_parameter(self, limit, expected_count):
        menu = make_menu(common={
            "dishes": [
                {"_id": f"d{i}", "image": make_image(url=f"https://cdn/d{i}.webp")}
                for i in range(5)
            ]
        })
        assert len(self.svc.extract_image_urls(menu, limit=limit)) == expected_count


@pytest.mark.unit
class TestResolveMeta:
    """
    Tests del método `resolve_meta(menu, key, locale, fallback)`.

    TODO (junior): implementar siguiendo el patrón de `TestExtractImageUrls`.

    Casos sugeridos:
    - test_returns_locale_meta_when_present
    - test_falls_back_to_fallback_locale_when_primary_missing
    - test_falls_back_to_common_meta_when_no_locale_matches
    - test_returns_none_when_no_meta_exists_anywhere
    """
    pass


# =============================================================================
# INTEGRATION TESTS — usan mongomock vía las fixtures `db`
# =============================================================================
@pytest.mark.integration
class TestAvailableOn:
    """
    Tests del método `available_on(locale, tzname, date_utc)`.

    TODO (junior): implementar usando `seed_menu(db, ...)` para sembrar datos
    y construir el service con `MenusService(MenusRepo(db), MenuTemplatesRepo(db))`.

    Casos sugeridos:
    - test_returns_menu_when_weekday_and_date_match
    - test_returns_empty_when_weekday_does_not_match
    - test_returns_empty_when_date_outside_range
    - test_respects_timezone_when_calculating_weekday
    - test_only_returns_menus_with_published_locale
    """

    def _svc(self, db):
        """Helper: crea el service con repos apuntando a mongomock."""
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    # Ejemplo mínimo para que el junior vea el patrón. Déjalo y escribe los demás.
    def test_returns_menu_when_weekday_and_date_match(self, db):
        from datetime import datetime, timezone
        seed_menu(db, availability={
            "timezone": "Europe/Madrid",
            "days_of_week": ["SAT"],
            "date_ranges": [{"start": "2025-09-01", "end": "2025-12-31"}],
        })
        # Sábado 2025-09-27 a las 12:00 UTC
        result = self._svc(db).available_on(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )
        assert len(result) == 1


@pytest.mark.integration
class TestMergeMenu:
    """
    Tests de `_merge_menu` y `_deep_merge_sections`.

    TODO (junior): estos métodos son privados pero críticos (fusión common+locale).

    Casos sugeridos:
    - test_merges_by_id_in_list_items
    - test_override_takes_precedence_over_base
    - test_preserves_common_fields_not_in_locale
    - test_falls_back_to_fallback_locale_when_primary_empty
    """
    pass


@pytest.mark.integration
class TestRenderFeaturedMenus:
    """
    Tests de `render_featured_menus`.

    TODO (junior):
    - test_returns_only_featured_menus
    - test_respects_featured_order
    - test_includes_ui_manifest_when_include_ui_true
    - test_skips_menus_without_published_locale
    """
    pass
