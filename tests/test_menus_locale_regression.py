"""
Regresión de los tres bugs que reportó QA sobre el listado público y `/render`.

Escenario original: `/public/available` listaba menús correctamente, pero al entrar
al menú con el `locale_used` que devolvía el propio listado, `/render` respondía
**500 Internal Server Error**.

Los tres defectos:
  1. `_merge_menu` devolvía dos formas distintas → `result["data"]` → KeyError → 500.
  2. `effective_locale` devolvía el locale pedido como eco cuando no había ninguno
     publicado → `locale_used` mentía → el frontend pedía un idioma inexistente.
  3. `publish_locale` dejaba publicar un idioma sin contenido → creaba ese dato malo.
"""
import pytest

from aralar.repositories.menu_templates_repo import MenuTemplatesRepo
from aralar.repositories.menus_repo import MenusRepo
from aralar.services.menus_service import MenusService
from tests.factories import seed_menu, seed_template


def _svc(db):
    return MenusService(MenusRepo(db), MenuTemplatesRepo(db))


# Menú "roto" tal y como quedó en la base de datos ANTES del fix: el idioma consta
# como publicado pero no existe el bloque de contenido en `locales`.
LEGACY_BROKEN = {
    "locales": {},
    "publish": {"es-ES": {"status": "published", "published_at": "2026-08-04T19:32:35Z"}},
}


@pytest.mark.unit
class TestMergeMenuAlwaysReturnsSameShape:
    """Bug 1: la causa directa del 500."""

    def test_returns_data_and_meta_when_locale_is_missing(self):
        svc = MenusService(None, None)
        menu = {"common": {"header": {"titulo": "Hola"}}, "locales": {}}

        result = svc._merge_menu(menu, locale="es-ES")

        assert set(result) == {"data", "meta"}
        assert result["data"] == {"header": {"titulo": "Hola"}}
        assert result["meta"] == {}

    def test_returns_data_and_meta_when_locale_exists(self):
        svc = MenusService(None, None)
        menu = {
            "common": {"header": {"titulo": "Hola"}},
            "locales": {"es-ES": {"data": {}, "meta": {"title": "T"}}},
        }

        result = svc._merge_menu(menu, locale="es-ES")

        assert set(result) == {"data", "meta"}
        assert result["meta"] == {"title": "T"}

    def test_caller_can_always_unpack_without_keyerror(self):
        """Es exactamente lo que hace `render` y lo que reventaba."""
        svc = MenusService(None, None)
        for locales in ({}, {"es-ES": {"data": {}, "meta": {}}}, {"otro": {"data": {}}}):
            result = svc._merge_menu({"common": {}, "locales": locales}, locale="es-ES")
            data, meta = result["data"], result["meta"]  # no debe lanzar
            assert isinstance(data, dict) and isinstance(meta, dict)


@pytest.mark.integration
class TestRenderOnLegacyBrokenData:
    """El dato malo ya está en las bases de datos existentes: `/render` no puede
    reventar con esos menús aunque ya no se puedan volver a crear."""

    def test_render_does_not_crash(self, db):
        menu = seed_menu(db, **LEGACY_BROKEN)
        out = _svc(db).render(str(menu["_id"]), locale="es-ES")

        assert out["locale"] == "es-ES"
        assert out["data"] == {}
        assert out["meta"] == {}

    def test_render_returns_common_content(self, db):
        menu = seed_menu(db, common={"header": {"titulo": "Hola"}}, **LEGACY_BROKEN)
        out = _svc(db).render(str(menu["_id"]), locale="es-ES")

        assert out["data"] == {"header": {"titulo": "Hola"}}

    def test_endpoint_returns_200_not_500(self, client, db):
        """La reproducción literal del reporte de QA."""
        menu = seed_menu(db, **LEGACY_BROKEN)
        res = client.get(f"/api/menus/{menu['_id']}/render?locale=es-ES")

        assert res.status_code == 200


@pytest.mark.unit
class TestEffectiveLocaleNeverLies:
    """Bug 2: `locale_used` debe ser un idioma que `/render` acepte."""

    def test_returns_none_when_nothing_is_published(self):
        svc = MenusService(None, None)
        assert svc.effective_locale({"publish": {}}, "fr") is None
        assert svc.effective_locale({}, "fr") is None

    def test_does_not_echo_the_requested_locale(self):
        """Antes devolvía 'fr' aunque el menú no tuviera nada publicado."""
        svc = MenusService(None, None)
        menu = {"publish": {"es-ES": {"status": "draft"}}}
        assert svc.effective_locale(menu, "fr") is None

    def test_falls_back_to_the_published_locale(self):
        svc = MenusService(None, None)
        menu = {"publish": {"es-ES": {"status": "published"}}}
        assert svc.effective_locale(menu, "fr") == "es-ES"

    def test_prefers_the_requested_locale(self):
        svc = MenusService(None, None)
        menu = {
            "publish": {
                "es-ES": {"status": "published"},
                "fr": {"status": "published"},
            }
        }
        assert svc.effective_locale(menu, "fr") == "fr"


@pytest.mark.e2e
class TestPublicListingOnlyReturnsRenderableMenus:
    def test_menu_without_published_locale_is_omitted(self, client, db):
        seed_menu(db, name="Sin idioma", locales={}, publish={})
        res = client.get("/api/menus/public/available?locale=fr")

        assert res.status_code == 200
        assert res.json["items"] == []

    def test_menu_with_published_locale_is_listed_with_fallback(self, client, db):
        """El requisito original: listar aunque el idioma pedido no exista."""
        seed_menu(db, name="Con es-ES")
        res = client.get("/api/menus/public/available?locale=fr")

        assert len(res.json["items"]) == 1
        assert res.json["items"][0]["locale_used"] == "es-ES"

    def test_every_listed_locale_used_can_be_rendered(self, client, db):
        """El contrato completo de punta a punta: lo que devuelve el listado
        sirve tal cual para llamar a /render."""
        seed_menu(db, name="A")
        seed_menu(db, name="B", locales={}, publish={})  # roto: debe omitirse

        listing = client.get("/api/menus/public/available?locale=fr")
        assert len(listing.json["items"]) == 1

        for item in listing.json["items"]:
            render = client.get(
                f"/api/menus/{item['id']}/render?locale={item['locale_used']}"
            )
            assert render.status_code == 200, f"render fallo para {item['name']}"


@pytest.mark.integration
class TestPublishLocaleRequiresContent:
    """Bug 3: el habilitador. Sin esto se sigue generando el dato malo."""

    def test_conflict_when_locale_has_no_content(self, db):
        menu = seed_menu(db, locales={}, publish={})
        res = _svc(db).publish_locale(str(menu["_id"]), "fr")

        assert isinstance(res, dict) and "conflict" in res
        assert db["menus"].find_one({"_id": menu["_id"]})["publish"] == {}

    def test_conflict_when_locale_block_is_empty(self, db):
        menu = seed_menu(db, locales={"fr": {"data": {}, "meta": {}}}, publish={})
        res = _svc(db).publish_locale(str(menu["_id"]), "fr")

        assert isinstance(res, dict) and "conflict" in res

    def test_publishes_when_there_is_content(self, db):
        menu = seed_menu(db, locales={"fr": {"data": {}, "meta": {"title": "Le menu"}}}, publish={})
        _svc(db).publish_locale(str(menu["_id"]), "fr")

        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["publish"]["fr"]["status"] == "published"

    def test_returns_none_for_missing_menu(self, db):
        from bson import ObjectId

        assert _svc(db).publish_locale(str(ObjectId()), "fr") is None


@pytest.mark.integration
class TestMetaIsNeverNull:
    """`update_locale` guardaba `meta: null` si no se le pasaba meta, y `/render`
    devolvía `"meta": null` en vez de `{}`."""

    def test_update_locale_without_meta_stores_empty_dict(self, db):
        menu = seed_menu(db, locales={})
        _svc(db).update_locale(str(menu["_id"]), "es-ES", {"name": "X"})

        stored = db["menus"].find_one({"_id": menu["_id"]})
        assert stored["locales"]["es-ES"]["meta"] == {}

    def test_render_never_returns_null_meta(self, db):
        menu = seed_menu(db, locales={})
        _svc(db).update_locale(str(menu["_id"]), "es-ES", {"name": "X"})

        out = _svc(db).render(str(menu["_id"]), locale="es-ES")
        assert out["meta"] == {}

    def test_legacy_null_meta_is_read_as_empty_dict(self, db):
        """Los menús guardados antes del fix tienen `meta: null` en Mongo."""
        menu = seed_menu(db, locales={"es-ES": {"data": {"name": "X"}, "meta": None}})

        out = _svc(db).render(str(menu["_id"]), locale="es-ES")
        assert out["meta"] == {}


@pytest.mark.e2e
class TestMenuCannotBeBornPublished:
    """Un menú creado con `status: published` se colaba en el listado público sin
    pasar por `validate_menu` (availability + un locale publicado)."""

    PAYLOAD = {
        "tenant_id": "aralar",
        "name": "Menu Publico Test",
        "template_slug": "test-template",
        "template_version": 1,
        "status": "published",
        "common": {},
    }

    def test_status_is_rejected_as_unknown_field(self, client, db, auth_headers):
        seed_template(db)
        res = client.post("/api/menus", json=self.PAYLOAD, headers=auth_headers())
        assert res.status_code == 422

    def test_menu_is_created_as_draft(self, client, db, auth_headers):
        seed_template(db)
        payload = {k: v for k, v in self.PAYLOAD.items() if k != "status"}
        res = client.post("/api/menus", json=payload, headers=auth_headers())

        assert res.status_code == 201
        assert res.json["status"] == "draft"

    def test_service_ignores_status_even_on_direct_calls(self, db):
        seed_template(db)
        doc = _svc(db).create(dict(self.PAYLOAD))
        assert doc["status"] == "draft"


@pytest.mark.e2e
class TestQAGuideScenario:
    """Replica el guion de `docs/QA_FIX_LOCALE_RENDER.md` con los documentos exactos
    que allí se inyectan en Mongo, para que la guía no prometa algo que el código no
    cumple."""

    AVAILABILITY = {
        "timezone": "Europe/Madrid",
        "days_of_week": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        "date_ranges": [{"start": "2026-01-01", "end": "2027-12-31"}],
    }

    def _seed_all(self, db):
        # Menú A: correcto, publicado en es-ES con contenido.
        seed_menu(db, name="Menu A (bueno)", template_slug="qa-fix-locale",
                  availability=self.AVAILABILITY)
        # Menú B: idioma publicado pero sin bloque de contenido (el que daba 500).
        seed_menu(
            db, name="Menu B (roto: idioma publicado sin contenido)",
            template_slug="qa-fix-locale", availability=self.AVAILABILITY,
            common={"header": {"title": "Contenido comun"}}, locales={},
            publish={"es-ES": {"status": "published", "published_at": "2026-08-04T00:00:00Z"}},
        )
        # Menú C: ningún idioma publicado (el que inventaba locale_used).
        seed_menu(
            db, name="Menu C (roto: ningun idioma publicado)",
            template_slug="qa-fix-locale", availability=self.AVAILABILITY,
            common={}, locales={}, publish={},
        )

    def test_caso_2_listing_omits_menu_c_and_never_invents_a_locale(self, client, db):
        self._seed_all(db)
        items = client.get("/api/menus/public/available?locale=fr").json["items"]

        nombres = {i["name"] for i in items}
        assert "Menu C (roto: ningun idioma publicado)" not in nombres
        assert len(items) == 2
        assert all(i["locale_used"] == "es-ES" for i in items)

    def test_caso_3_every_listed_item_renders_with_its_locale_used(self, client, db):
        """El contrato completo: lo que devuelve el listado sirve tal cual para /render."""
        self._seed_all(db)
        items = client.get("/api/menus/public/available?locale=fr").json["items"]

        for item in items:
            res = client.get(f"/api/menus/{item['id']}/render?locale={item['locale_used']}")
            assert res.status_code == 200, f"render fallo para {item['name']}"

    def test_caso_1_broken_menu_renders_its_common_content(self, client, db):
        self._seed_all(db)
        items = client.get("/api/menus/public/available?locale=fr").json["items"]
        menu_b = [i for i in items if i["name"].startswith("Menu B")][0]

        res = client.get(f"/api/menus/{menu_b['id']}/render?locale=es-ES")

        assert res.status_code == 200
        assert res.json["data"] == {"header": {"title": "Contenido comun"}}
        assert res.json["meta"] == {}


@pytest.mark.e2e
class TestPublishLocaleEndpoint:
    def test_returns_409_without_content(self, client, db, auth_headers):
        menu = seed_menu(db, locales={}, publish={})
        res = client.post(f"/api/menus/{menu['_id']}/publish/fr", headers=auth_headers())

        assert res.status_code == 409

    def test_returns_200_with_content(self, client, db, auth_headers):
        menu = seed_menu(db, locales={"fr": {"data": {}, "meta": {"title": "Le menu"}}}, publish={})
        res = client.post(f"/api/menus/{menu['_id']}/publish/fr", headers=auth_headers())

        assert res.status_code == 200
