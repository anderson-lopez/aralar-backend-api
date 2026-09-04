"""
Tests de `aralar.services.menu_services_service.MenuServicesService`.

Cubre el CRUD del catálogo de servicios (colección `menu_services`): creación
con slug único por tenant, normalización de slug, actualización, borrado
bloqueado por referencia de menús, y el listado público de servicios activos.
"""
import pytest

from aralar.services.menu_services_service import MenuServicesService
from aralar.repositories.menu_services_repo import MenuServicesRepo
from aralar.repositories.menus_repo import MenusRepo
from tests.factories import seed_menu_service, seed_menu


def _svc(db):
    return MenuServicesService(MenuServicesRepo(db))


@pytest.mark.integration
class TestCreate:
    def test_creates_service(self, db):
        res = _svc(db).create({
            "tenant_id": "aralar", "slug": "desayunos", "name": "Desayunos",
        })
        assert res["slug"] == "desayunos"
        assert res["is_active"] is True

    def test_normalizes_slug(self, db):
        res = _svc(db).create({
            "tenant_id": "aralar", "slug": "  Comida Para Llevar ", "name": "X",
        })
        assert res["slug"] == "comida-para-llevar"

    def test_rejects_duplicate_slug_same_tenant(self, db):
        seed_menu_service(db, slug="desayunos")
        res = _svc(db).create({
            "tenant_id": "aralar", "slug": "desayunos", "name": "Otro",
        })
        assert isinstance(res, dict) and res.get("conflict")

    def test_same_slug_allowed_for_different_tenant(self, db):
        seed_menu_service(db, tenant_id="aralar", slug="desayunos")
        res = _svc(db).create({
            "tenant_id": "otro", "slug": "desayunos", "name": "Desayunos",
        })
        assert res.get("slug") == "desayunos"


@pytest.mark.integration
class TestListAndGet:
    def test_list_filters_by_active(self, db):
        seed_menu_service(db, slug="a", is_active=True)
        seed_menu_service(db, slug="b", is_active=False)
        res = _svc(db).list({"is_active": True})
        slugs = [s["slug"] for s in res["items"]]
        assert slugs == ["a"]
        assert res["total"] == 1

    def test_list_orders_by_order_then_name(self, db):
        seed_menu_service(db, slug="b", name="B", order=2)
        seed_menu_service(db, slug="a", name="A", order=1)
        res = _svc(db).list({})
        assert [s["slug"] for s in res["items"]] == ["a", "b"]


@pytest.mark.integration
class TestUpdate:
    def test_updates_fields(self, db):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = _svc(db).update(sid, {"name": "Nuevo", "order": 9})
        assert res["name"] == "Nuevo"
        assert res["order"] == 9

    def test_returns_none_when_missing(self, db):
        from bson import ObjectId
        assert _svc(db).update(str(ObjectId()), {"name": "x"}) is None

    def test_slug_is_immutable(self, db):
        """El slug no se puede cambiar: los menús lo referencian sin cascada y
        renombrarlo los dejaría huérfanos (fuera de available Y de su servicio)."""
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = _svc(db).update(sid, {"slug": "otro", "name": "Nuevo"})
        assert res["slug"] == "desayunos"
        assert res["name"] == "Nuevo"

    def test_deactivating_reports_affected_menus(self, db):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        seed_menu(db, service_slugs=["desayunos"])
        seed_menu(db, service_slugs=["desayunos"])
        res = _svc(db).update(sid, {"is_active": False}, menus_repo=MenusRepo(db))
        assert res["is_active"] is False
        assert res["affected_menus"] == 2

    def test_deactivating_without_menus_has_no_warning(self, db):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = _svc(db).update(sid, {"is_active": False}, menus_repo=MenusRepo(db))
        assert "affected_menus" not in res

    def test_plain_update_has_no_warning(self, db):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        seed_menu(db, service_slugs=["desayunos"])
        res = _svc(db).update(sid, {"name": "X"}, menus_repo=MenusRepo(db))
        assert "affected_menus" not in res


@pytest.mark.integration
class TestDelete:
    def test_deletes_when_not_referenced(self, db):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        res = _svc(db).delete(sid, menus_repo=MenusRepo(db))
        assert res == {"ok": True}

    def test_blocked_when_referenced_by_menu(self, db):
        sid = str(seed_menu_service(db, slug="desayunos")["_id"])
        seed_menu(db, service_slugs=["desayunos"])
        res = _svc(db).delete(sid, menus_repo=MenusRepo(db))
        assert isinstance(res, dict) and res.get("conflict")

    def test_returns_none_when_missing(self, db):
        from bson import ObjectId
        assert _svc(db).delete(str(ObjectId()), menus_repo=MenusRepo(db)) is None


@pytest.mark.integration
class TestPublicList:
    def test_returns_only_active_ordered(self, db):
        seed_menu_service(db, slug="b", name="B", order=2, is_active=True)
        seed_menu_service(db, slug="a", name="A", order=1, is_active=True)
        seed_menu_service(db, slug="off", is_active=False)
        res = _svc(db).public_list(tenant_id="aralar")
        assert [s["slug"] for s in res["items"]] == ["a", "b"]

    def test_resolves_label_by_locale(self, db):
        seed_menu_service(db, slug="desayunos", labels={"es-ES": "Desayunos", "en-GB": "Breakfast"})
        res = _svc(db).public_list(tenant_id="aralar", locale="en-GB")
        assert res["items"][0]["label"] == "Breakfast"

    def test_label_falls_back_to_any_or_name(self, db):
        seed_menu_service(db, slug="desayunos", name="Desayunos", labels={})
        res = _svc(db).public_list(tenant_id="aralar", locale="fr-FR")
        assert res["items"][0]["label"] == "Desayunos"
