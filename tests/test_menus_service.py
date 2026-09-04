"""
Tests de `aralar.services.menus_service.MenusService`.

Este archivo combina DOS tipos de tests:

1. UNIT tests (clases `TestExtractImageUrls`, `TestResolveMeta`)
   → No tocan Mongo ni Flask. Construyen dicts en memoria y verifican la
     salida pura de un método. Son los más rápidos y los que más deberías
     escribir para lógica de negocio determinística.

2. INTEGRATION tests (clases `TestAvailableOn`, `TestMergeMenu`, ...)
   → Usan las fixtures `db` y las factories para sembrar datos en mongomock
     y verificar que el service + repo funcionan juntos correctamente.

Patrón:
- Agrupa por método en una `class TestNombreDelMetodo:`.
- Un test = un escenario. Nombre: `test_<metodo>_<escenario>_<resultado>`.
- Usa `@pytest.mark.parametrize` cuando varios casos comparten lógica y solo
  cambian los inputs/outputs.
- Usa `make_menu`, `make_image`, `seed_menu` de `tests.factories` en vez de
  escribir dicts gigantes inline.
"""
from datetime import datetime, timezone

import pytest

from aralar.services.menus_service import MenusService
from aralar.repositories.menus_repo import MenusRepo
from aralar.repositories.menu_templates_repo import MenuTemplatesRepo
from aralar.repositories.menu_services_repo import MenuServicesRepo

from tests.factories import make_menu, make_image, seed_menu, seed_template, seed_menu_service


# =============================================================================
# UNIT TESTS — no tocan Mongo ni Flask
# =============================================================================
@pytest.mark.unit
class TestExtractImageUrls:
    """
    Tests del método `extract_image_urls(menu_doc, limit)`.

    Este método recorre `common` recursivamente y devuelve URLs de imagen
    (dicts con clave `url` string, opcionalmente filtrados por `mime`).
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

    @pytest.mark.parametrize("limit,expected_count", [(1, 1), (2, 2), (3, 3), (10, 5)])
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

    Devuelve el valor de `locales[locale].meta[key]`, cae a
    `locales[fallback].meta[key]`, y si no existe ninguno, a
    `common.meta[key]`. Devuelve None si no hay valor en ninguno.
    """

    def setup_method(self):
        self.svc = MenusService(repo=None, templates_repo=None)

    def test_returns_locale_meta_when_present(self):
        menu = make_menu(locales={
            "es-ES": {"data": {}, "meta": {"title": "Título ES"}},
        })
        assert self.svc.resolve_meta(menu, "title", "es-ES") == "Título ES"

    def test_falls_back_to_fallback_locale_when_primary_missing(self):
        menu = make_menu(locales={
            "es-ES": {"data": {}, "meta": {"title": "Título ES"}},
        })
        # en-GB no existe → cae a es-ES
        assert self.svc.resolve_meta(menu, "title", "en-GB", fallback="es-ES") == "Título ES"

    def test_falls_back_to_common_meta_when_no_locale_matches(self):
        menu = make_menu(
            common={"meta": {"title": "Title Common"}},
            locales={},
        )
        assert self.svc.resolve_meta(menu, "title", "es-ES") == "Title Common"

    def test_returns_none_when_no_meta_exists_anywhere(self):
        menu = make_menu(common={}, locales={})
        assert self.svc.resolve_meta(menu, "title", "es-ES") is None


@pytest.mark.unit
class TestEffectiveLocale:
    """
    Tests de `effective_locale(menu, locale, fallback)`.

    Cascada: locale pedido (si publicado) → fallback explícito (si publicado)
    → primer locale publicado del menú. Solo cuentan locales con
    `publish.{loc}.status == "published"`.
    """

    def setup_method(self):
        self.svc = MenusService(repo=None, templates_repo=None)

    def test_returns_requested_locale_when_published(self):
        menu = make_menu(publish={
            "es-ES": {"status": "published"},
            "en-GB": {"status": "published"},
        })
        assert self.svc.effective_locale(menu, "en-GB") == "en-GB"

    def test_falls_back_to_first_published_when_requested_missing(self):
        menu = make_menu(publish={"es-ES": {"status": "published"}})
        # en-GB no publicado → cae al único publicado (es-ES)
        assert self.svc.effective_locale(menu, "en-GB") == "es-ES"

    def test_prefers_explicit_fallback_over_default(self):
        menu = make_menu(publish={
            "es-ES": {"status": "published"},
            "en-GB": {"status": "published"},
        })
        # fr-FR ausente, fallback en-GB publicado → en-GB (no el primero es-ES)
        assert self.svc.effective_locale(menu, "fr-FR", fallback="en-GB") == "en-GB"

    def test_ignores_non_published_locales(self):
        menu = make_menu(publish={
            "es-ES": {"status": "draft"},
            "en-GB": {"status": "published"},
        })
        # es-ES está en draft → no cuenta; cae a en-GB
        assert self.svc.effective_locale(menu, "fr-FR") == "en-GB"


@pytest.mark.unit
class TestDeepMergeSections:
    """
    Tests del método privado `_deep_merge_sections(base, override)`.

    Reglas:
    - Si una clave existe en common con valor no vacío, gana common.
    - Las listas con _id se mergean por _id.
    - Las claves que solo están en override (locale) se preservan.
    """

    def setup_method(self):
        self.svc = MenusService(repo=None, templates_repo=None)

    def test_merges_by_id_in_list_items(self):
        base = [
            {"_id": "a", "name": "A common"},
            {"_id": "b", "name": "B common"},
        ]
        override = [
            {"_id": "a", "description": "A desc loc"},
            {"_id": "b", "description": "B desc loc"},
        ]
        result = self.svc._deep_merge_sections(base, override)
        # Cada item tiene su name (common) Y su description (locale).
        result_by_id = {x["_id"]: x for x in result}
        assert result_by_id["a"] == {"_id": "a", "name": "A common", "description": "A desc loc"}
        assert result_by_id["b"] == {"_id": "b", "name": "B common", "description": "B desc loc"}

    def test_common_wins_over_locale_when_both_have_value(self):
        """Regresión del fix: stale data en locale ya no pisa common."""
        base = {"image": {"url": "https://cdn/new.webp"}}
        override = {"image": {"url": "https://cdn/old.webp"}}
        result = self.svc._deep_merge_sections(base, override)
        assert result["image"]["url"] == "https://cdn/new.webp"

    def test_preserves_locale_fields_not_in_common(self):
        """Campos que solo viven en locale (traducibles) se conservan."""
        base = {"price": 10}
        override = {"description": "Texto localizado"}
        result = self.svc._deep_merge_sections(base, override)
        assert result == {"price": 10, "description": "Texto localizado"}

    def test_override_fills_in_when_common_value_is_empty(self):
        """Si common está vacío o None en esa clave, el locale rellena."""
        base = {"description": ""}
        override = {"description": "Texto del locale"}
        result = self.svc._deep_merge_sections(base, override)
        assert result["description"] == "Texto del locale"

    def test_ignores_new_items_in_override_list(self):
        """Items que solo existen en locale (sin _id en common) se ignoran."""
        base = [{"_id": "a", "name": "A"}]
        override = [{"_id": "a", "desc": "A desc"}, {"_id": "x", "desc": "X solo locale"}]
        result = self.svc._deep_merge_sections(base, override)
        ids = [x["_id"] for x in result]
        assert "x" not in ids
        assert "a" in ids


# =============================================================================
# INTEGRATION TESTS — usan mongomock vía las fixtures `db`
# =============================================================================
@pytest.mark.integration
class TestAvailableOn:
    """
    Tests del método `available_on(locale, tzname, date_utc)`.

    Devuelve los menús publicados para el locale cuyo `availability` incluye
    el weekday y la fecha (en el timezone indicado).
    """

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_menu_when_weekday_and_date_match(self, db):
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

    def test_returns_empty_when_weekday_does_not_match(self, db):
        seed_menu(db, availability={
            "timezone": "Europe/Madrid",
            "days_of_week": ["SAT"],  # solo sábados
            "date_ranges": [{"start": "2025-09-01", "end": "2025-12-31"}],
        })
        # Lunes 2025-09-29 — no incluye SAT.
        result = self._svc(db).available_on(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 29, 12, 0, tzinfo=timezone.utc),
        )
        assert result == []

    def test_returns_empty_when_date_outside_range(self, db):
        seed_menu(db, availability={
            "timezone": "Europe/Madrid",
            "days_of_week": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
            "date_ranges": [{"start": "2025-09-01", "end": "2025-09-30"}],
        })
        # Fuera del rango → octubre.
        result = self._svc(db).available_on(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 10, 15, 12, 0, tzinfo=timezone.utc),
        )
        assert result == []

    def test_returns_menu_even_when_requested_locale_not_published(self, db):
        """Nuevo requerimiento: el listado no filtra por idioma. Un menú publicado
        globalmente sale aunque el locale pedido no exista para él (el idioma
        efectivo se resuelve aparte con `effective_locale`)."""
        seed_menu(
            db,
            publish={"en-GB": {"status": "published", "published_at": datetime.now(timezone.utc)}},
            locales={"en-GB": {"data": {}, "meta": {"title": "EN"}}},
        )
        result = self._svc(db).available_on(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )
        assert len(result) == 1


@pytest.mark.integration
class TestAvailableOnOrdering:
    """
    Tests del orden del listado público (`available_on`), regido por `list_order`.

    Reglas: `list_order` asc (menor = más prioritario) → los `None` al final →
    empates desempatados por `updated_at` desc.
    """

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def _available(self, db):
        return self._svc(db).available_on(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )

    def test_orders_by_list_order_ascending(self, db):
        seed_menu(db, name="tercero", list_order=3)
        seed_menu(db, name="primero", list_order=1)
        seed_menu(db, name="segundo", list_order=2)

        names = [m["name"] for m in self._available(db)]
        assert names == ["primero", "segundo", "tercero"]

    def test_menus_without_list_order_go_last(self, db):
        seed_menu(db, name="sin orden", list_order=None)
        seed_menu(db, name="con orden", list_order=5)

        names = [m["name"] for m in self._available(db)]
        assert names == ["con orden", "sin orden"]

    def test_ties_broken_by_updated_at_desc(self, db):
        seed_menu(
            db,
            name="viejo",
            list_order=1,
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        )
        seed_menu(
            db,
            name="reciente",
            list_order=1,
            updated_at=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )

        names = [m["name"] for m in self._available(db)]
        assert names == ["reciente", "viejo"]

    def test_falls_back_to_updated_at_when_no_menu_has_order(self, db):
        seed_menu(db, name="viejo", updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc))
        seed_menu(db, name="reciente", updated_at=datetime(2025, 6, 1, tzinfo=timezone.utc))

        names = [m["name"] for m in self._available(db)]
        assert names == ["reciente", "viejo"]

    def test_zero_is_a_valid_order_and_beats_null(self, db):
        """`0` es un valor legítimo y no debe confundirse con 'sin orden'."""
        seed_menu(db, name="sin orden", list_order=None)
        seed_menu(db, name="cero", list_order=0)

        names = [m["name"] for m in self._available(db)]
        assert names == ["cero", "sin orden"]

    def test_negative_order_comes_first(self, db):
        seed_menu(db, name="normal", list_order=1)
        seed_menu(db, name="destacado", list_order=-10)

        names = [m["name"] for m in self._available(db)]
        assert names == ["destacado", "normal"]


@pytest.mark.integration
class TestCreateRequiresPublishedTemplate:
    """
    Un menú solo puede instanciarse sobre una plantilla **publicada**.

    Sobre un draft sería peligroso: el draft sí se puede editar y el menú
    quedaría atado a una estructura que cambia bajo sus pies.
    """

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def _payload(self):
        return {
            "tenant_id": "aralar", "name": "M",
            "template_slug": "test-template", "template_version": 1, "common": {},
        }

    def test_creates_on_published_template(self, db):
        seed_template(db, status="published")
        res = self._svc(db).create(self._payload())
        assert res.get("_id")

    def test_rejects_draft_template(self, db):
        seed_template(db, status="draft")
        res = self._svc(db).create(self._payload())
        assert isinstance(res, dict) and res.get("error")

    def test_rejects_archived_template(self, db):
        seed_template(db, status="archived")
        res = self._svc(db).create(self._payload())
        assert isinstance(res, dict) and res.get("error")

    def test_returns_none_when_template_missing(self, db):
        assert self._svc(db).create(self._payload()) is None


@pytest.mark.integration
class TestServiceClassification:
    """
    Clasificación en "Otros servicios" (`service_slugs`).

    Un menú con `service_slugs` no vacío queda FUERA de `available_on` y solo
    aparece en `service_menus_on(service_slug, ...)`.
    """

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def _available(self, db):
        return self._svc(db).available_on(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )

    def _service(self, db, slug):
        return self._svc(db).service_menus_on(
            slug,
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )

    def test_available_excludes_menus_with_services(self, db):
        seed_menu(db, name="normal", service_slugs=[])
        seed_menu(db, name="clasificado", service_slugs=["desayunos"])

        names = [m["name"] for m in self._available(db)]
        assert names == ["normal"]

    def test_available_includes_menu_with_missing_service_field(self, db):
        """Un menú legacy sin el campo `service_slugs` debe seguir apareciendo."""
        m = make_menu(name="legacy")
        m.pop("service_slugs", None)
        db["menus"].insert_one(m)

        names = [x["name"] for x in self._available(db)]
        assert names == ["legacy"]

    def test_service_menus_returns_only_matching_service(self, db):
        seed_menu(db, name="desayuno", service_slugs=["desayunos"])
        seed_menu(db, name="lunch", service_slugs=["lunch"])
        seed_menu(db, name="normal", service_slugs=[])

        names = [m["name"] for m in self._service(db, "desayunos")]
        assert names == ["desayuno"]

    def test_service_menus_matches_any_slug_in_array(self, db):
        seed_menu(db, name="mixto", service_slugs=["desayunos", "lunch"])

        assert [m["name"] for m in self._service(db, "desayunos")] == ["mixto"]
        assert [m["name"] for m in self._service(db, "lunch")] == ["mixto"]

    def test_service_menus_respects_list_order(self, db):
        seed_menu(db, name="b", service_slugs=["desayunos"], list_order=2)
        seed_menu(db, name="a", service_slugs=["desayunos"], list_order=1)

        names = [m["name"] for m in self._service(db, "desayunos")]
        assert names == ["a", "b"]

    def test_service_menus_empty_for_unknown_slug(self, db):
        seed_menu(db, name="desayuno", service_slugs=["desayunos"])
        assert self._service(db, "cena") == []


@pytest.mark.integration
class TestResolveServiceSlugs:
    """
    Validación de `service_slugs` en create/update (`_resolve_service_slugs`).

    Requiere `services_repo` para validar existencia/estado; sin él, no valida.
    """

    def _svc(self, db):
        return MenusService(
            MenusRepo(db), MenuTemplatesRepo(db), MenuServicesRepo(db)
        )

    def test_create_rejects_unknown_service(self, db):
        seed_template(db)
        res = self._svc(db).create({
            "tenant_id": "aralar",
            "name": "M",
            "template_slug": "test-template",
            "template_version": 1,
            "common": {},
            "service_slugs": ["inexistente"],
        })
        assert isinstance(res, dict) and res.get("error")

    def test_create_accepts_known_active_service(self, db):
        seed_template(db)
        seed_menu_service(db, slug="desayunos")
        res = self._svc(db).create({
            "tenant_id": "aralar",
            "name": "M",
            "template_slug": "test-template",
            "template_version": 1,
            "common": {},
            "service_slugs": ["desayunos"],
        })
        assert res.get("service_slugs") == ["desayunos"]

    def test_create_rejects_inactive_service(self, db):
        seed_template(db)
        seed_menu_service(db, slug="desayunos", is_active=False)
        res = self._svc(db).create({
            "tenant_id": "aralar",
            "name": "M",
            "template_slug": "test-template",
            "template_version": 1,
            "common": {},
            "service_slugs": ["desayunos"],
        })
        assert isinstance(res, dict) and res.get("error")

    def test_create_normalizes_and_dedups_slugs(self, db):
        seed_template(db)
        seed_menu_service(db, slug="desayunos")
        res = self._svc(db).create({
            "tenant_id": "aralar",
            "name": "M",
            "template_slug": "test-template",
            "template_version": 1,
            "common": {},
            "service_slugs": ["  Desayunos ", "desayunos"],
        })
        assert res.get("service_slugs") == ["desayunos"]

    def test_duplicate_inherits_service_slugs(self, db):
        seed_template(db)
        seed_menu_service(db, slug="desayunos")
        m = seed_menu(db, name="orig", service_slugs=["desayunos"])
        copy = self._svc(db).duplicate(str(m["_id"]))
        assert copy["service_slugs"] == ["desayunos"]


@pytest.mark.integration
class TestMergeMenu:
    """
    Tests del método `_merge_menu(menu_doc, locale, fallback)`.

    Devuelve `{"data": merged, "meta": meta}` cuando existe el locale.
    """

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_data_and_meta_for_existing_locale(self, db):
        svc = self._svc(db)
        menu = make_menu(
            common={"dishes": [{"_id": "d1", "image": {"url": "https://cdn/a.webp"}}]},
            locales={"es-ES": {"data": {"dishes": [{"_id": "d1", "name": "Plato"}]},
                                "meta": {"title": "T"}}},
        )
        result = svc._merge_menu(menu, locale="es-ES")
        assert result["meta"] == {"title": "T"}
        # El item d1 trae image (común) + name (locale)
        dishes = result["data"]["dishes"]
        assert dishes[0]["image"]["url"] == "https://cdn/a.webp"
        assert dishes[0]["name"] == "Plato"

    def test_falls_back_to_fallback_locale_when_primary_missing(self, db):
        svc = self._svc(db)
        menu = make_menu(
            common={},
            locales={"es-ES": {"data": {"x": "valor ES"}, "meta": {"title": "T ES"}}},
        )
        # Pedimos en-GB, no existe → cae a es-ES.
        result = svc._merge_menu(menu, locale="en-GB", fallback="es-ES")
        assert result["data"]["x"] == "valor ES"
        assert result["meta"]["title"] == "T ES"

    def test_common_value_wins_over_locale_in_merge(self, db):
        svc = self._svc(db)
        menu = make_menu(
            common={"image": {"url": "https://cdn/new.webp"}},
            locales={"es-ES": {"data": {"image": {"url": "https://cdn/old.webp"}},
                                "meta": {}}},
        )
        result = svc._merge_menu(menu, locale="es-ES")
        assert result["data"]["image"]["url"] == "https://cdn/new.webp"


@pytest.mark.integration
class TestRenderFeaturedMenus:
    """
    Tests de `render_featured_menus(locale, tzname, ...)`.
    """

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_only_featured_menus(self, db):
        seed_menu(db, name="Featured", featured=True, featured_order=1)
        seed_menu(db, name="Normal", featured=False)
        result = self._svc(db).render_featured_menus(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )
        names = [m["name"] for m in result]
        assert names == ["Featured"]

    def test_respects_featured_order(self, db):
        seed_menu(db, name="Segundo", featured=True, featured_order=20)
        seed_menu(db, name="Primero", featured=True, featured_order=10)
        seed_menu(db, name="Tercero", featured=True, featured_order=30)
        result = self._svc(db).render_featured_menus(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )
        assert [m["name"] for m in result] == ["Primero", "Segundo", "Tercero"]

    def test_includes_ui_manifest_when_include_ui_true(self, db):
        seed_template(db, slug="test-template", version=1)
        seed_menu(db, featured=True, featured_order=1)
        result = self._svc(db).render_featured_menus(
            locale="es-ES",
            tzname="Europe/Madrid",
            include_ui=True,
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )
        assert "ui" in result[0]
        assert result[0]["ui"]["layout"] == "sections"

    def test_skips_menus_without_published_locale(self, db):
        # Featured pero publicado solo en en-GB.
        seed_menu(
            db,
            name="Solo EN",
            featured=True,
            featured_order=1,
            publish={"en-GB": {"status": "published", "published_at": datetime.now(timezone.utc)}},
        )
        result = self._svc(db).render_featured_menus(
            locale="es-ES",
            tzname="Europe/Madrid",
            date_utc=datetime(2025, 9, 27, 12, 0, tzinfo=timezone.utc),
        )
        assert result == []


@pytest.mark.integration
class TestCreate:
    """Tests del método `create(data)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_none_when_template_does_not_exist(self, db):
        result = self._svc(db).create({
            "tenant_id": "aralar",
            "name": "Menu sin template",
            "template_slug": "no-existe",
            "template_version": 1,
        })
        assert result is None

    def test_creates_menu_when_template_exists(self, db):
        seed_template(db, slug="test-template", version=1)
        result = self._svc(db).create({
            "tenant_id": "aralar",
            "name": "Mi menú",
            "template_slug": "test-template",
            "template_version": 1,
        })
        assert result is not None
        assert result["name"] == "Mi menú"
        assert result["status"] == "draft"

    def test_persists_menu_in_database(self, db):
        seed_template(db, slug="test-template", version=1)
        self._svc(db).create({
            "tenant_id": "aralar",
            "name": "Persistido",
            "template_slug": "test-template",
            "template_version": 1,
        })
        assert db["menus"].count_documents({"name": "Persistido"}) == 1


@pytest.mark.integration
class TestList:
    """Tests del método `list(query_args)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_paginated_structure(self, db):
        seed_menu(db, name="A")
        seed_menu(db, name="B")
        result = self._svc(db).list({"skip": 0, "limit": 10})
        assert set(result.keys()) == {"items", "total", "skip", "limit"}
        assert result["total"] == 2

    def test_filters_by_status(self, db):
        seed_menu(db, name="Draft", status="draft")
        seed_menu(db, name="Published", status="published")
        result = self._svc(db).list({"status": "draft"})
        names = [m["name"] for m in result["items"]]
        assert names == ["Draft"]

    def test_respects_skip_and_limit(self, db):
        for i in range(5):
            seed_menu(db, name=f"Menu {i}")
        result = self._svc(db).list({"skip": 2, "limit": 2})
        assert len(result["items"]) == 2
        assert result["total"] == 5


@pytest.mark.integration
class TestPublishLocale:
    """Tests del método `publish_locale(menu_id, locale)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_none_when_menu_not_found(self, db):
        from bson import ObjectId
        result = self._svc(db).publish_locale(str(ObjectId()), "es-ES")
        assert result is None

    def test_marks_locale_as_published(self, db):
        menu = seed_menu(db, publish={})
        result = self._svc(db).publish_locale(str(menu["_id"]), "es-ES")
        assert result["publish"]["es-ES"]["status"] == "published"


@pytest.mark.integration
class TestValidateMenu:
    """Tests del método `validate_menu(menu_id)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_ok_when_availability_and_locale_published(self, db):
        menu = seed_menu(db)
        result = self._svc(db).validate_menu(str(menu["_id"]))
        assert result["ok"] is True
        assert result["issues"] == []

    def test_returns_issue_when_no_availability(self, db):
        menu = seed_menu(db, availability={})
        result = self._svc(db).validate_menu(str(menu["_id"]))
        assert result["ok"] is False
        assert "availability is required" in result["issues"]

    def test_returns_issue_when_no_locale_published(self, db):
        menu = seed_menu(db, publish={})
        result = self._svc(db).validate_menu(str(menu["_id"]))
        assert result["ok"] is False
        assert any("locale" in i for i in result["issues"])


@pytest.mark.integration
class TestDelete:
    """Tests del método `delete(menu_id)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_false_when_menu_not_found(self, db):
        from bson import ObjectId
        result = self._svc(db).delete(str(ObjectId()))
        assert result is False

    def test_returns_true_and_removes_when_menu_exists(self, db):
        menu = seed_menu(db)
        result = self._svc(db).delete(str(menu["_id"]))
        assert result is True
        assert db["menus"].count_documents({}) == 0


@pytest.mark.integration
class TestDuplicate:
    """Tests del método `duplicate(menu_id, name)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_returns_none_when_menu_not_found(self, db):
        from bson import ObjectId
        assert self._svc(db).duplicate(str(ObjectId())) is None

    def test_copies_content_and_resets_state(self, db):
        menu = seed_menu(
            db,
            name="Original",
            status="published",
            featured=True,
            featured_order=3,
            common={"items": [{"_id": "i1", "price": 5}]},
            locales={"es-ES": {"data": {"items": [{"_id": "i1", "name": "Plato"}]},
                               "meta": {"title": "T"}}},
        )
        dup = self._svc(db).duplicate(str(menu["_id"]))
        # Contenido reutilizable copiado.
        assert dup["common"] == {"items": [{"_id": "i1", "price": 5}]}
        assert dup["locales"]["es-ES"]["data"]["items"][0]["name"] == "Plato"
        assert dup["availability"] == menu["availability"]
        assert dup["template_slug"] == menu["template_slug"]
        # Estado reseteado.
        assert dup["status"] == "draft"
        assert dup["publish"] == {}
        assert dup["featured"] is False
        assert dup["featured_order"] is None
        # Nombre por defecto.
        assert dup["name"] == "Original (copia)"

    def test_uses_custom_name_when_provided(self, db):
        menu = seed_menu(db, name="Original")
        dup = self._svc(db).duplicate(str(menu["_id"]), name="Copia especial")
        assert dup["name"] == "Copia especial"

    def test_creates_a_new_document(self, db):
        menu = seed_menu(db)
        dup = self._svc(db).duplicate(str(menu["_id"]))
        assert dup["_id"] != menu["_id"]
        assert db["menus"].count_documents({}) == 2

    def test_does_not_mutate_original(self, db):
        menu = seed_menu(db, status="published", featured=True, featured_order=1)
        self._svc(db).duplicate(str(menu["_id"]))
        original = db["menus"].find_one({"_id": menu["_id"]})
        assert original["status"] == "published"
        assert original["featured"] is True

    def test_deep_copies_nested_structures(self, db):
        menu = seed_menu(db, common={"items": [{"_id": "i1", "price": 5}]})
        dup = self._svc(db).duplicate(str(menu["_id"]))
        # Mutar la copia no debe afectar al original en DB.
        dup["common"]["items"][0]["price"] = 999
        original = db["menus"].find_one({"_id": menu["_id"]})
        assert original["common"]["items"][0]["price"] == 5


@pytest.mark.integration
class TestUpdateFeatured:
    """Tests del método `update_featured(menu_id, featured, featured_order)`."""

    def _svc(self, db):
        return MenusService(MenusRepo(db), MenuTemplatesRepo(db))

    def test_sets_featured_true_with_order(self, db):
        menu = seed_menu(db, featured=False, featured_order=None)
        result = self._svc(db).update_featured(str(menu["_id"]), featured=True, featured_order=5)
        assert result["featured"] is True
        assert result["featured_order"] == 5

    def test_clears_order_when_unfeaturing(self, db):
        menu = seed_menu(db, featured=True, featured_order=5)
        result = self._svc(db).update_featured(str(menu["_id"]), featured=False)
        assert result["featured"] is False
        assert result["featured_order"] is None
