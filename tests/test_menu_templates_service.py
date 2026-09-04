"""
Tests de `aralar.services.menu_templates_service.MenuTemplatesService`.

Cubre la lógica de creación, publicación, versionado, listado y borrado de
templates. Los templates son la base de los menús: definen qué secciones y
campos tienen.

Convenciones del service (relevantes para entender los tests):
- `create()` devuelve un string `_id` si OK, o `{"conflict": str}` si choca con
  un (slug, version) ya existente.
- `publish()`:
    - Si el template está en `draft`, lo marca como `published` y devuelve su ID.
    - Si ya está `published`, crea un NUEVO documento con `version` siguiente y
      devuelve el nuevo ID. No muta el documento original.
    - Devuelve `None` si no existe.
- `update_draft()` solo permite editar drafts; si está published devuelve
  `{"conflict": ...}`.
"""
import pytest

from aralar.services.menu_templates_service import MenuTemplatesService
from aralar.repositories.menu_templates_repo import MenuTemplatesRepo
from aralar.repositories.menus_repo import MenusRepo

from tests.factories import make_template, seed_template, seed_menu


def _svc(db):
    """Helper: crea el service con repo apuntando a mongomock."""
    return MenuTemplatesService(MenuTemplatesRepo(db))


@pytest.mark.integration
class TestCreateTemplate:
    """
    Tests de `create(data)`.
    """

    def test_creates_template_with_status_draft_by_default(self, db):
        tmpl_data = make_template(slug="nuevo", version=1, status=None)
        tmpl_data.pop("status", None)  # Forzar default
        new_id = _svc(db).create(tmpl_data)
        assert isinstance(new_id, str)
        stored = db["menu_templates"].find_one({"slug": "nuevo"})
        assert stored["status"] == "draft"

    def test_returns_conflict_when_slug_version_already_exists(self, db):
        seed_template(db, slug="repetido", version=1)
        result = _svc(db).create(make_template(slug="repetido", version=1))
        assert isinstance(result, dict)
        assert "conflict" in result

    def test_accepts_multiple_locales_in_i18n_config(self, db):
        tmpl_data = make_template(
            slug="i18n-template",
            i18n={"default_locale": "es-ES", "locales": ["es-ES", "en-GB", "eu-ES"]},
        )
        new_id = _svc(db).create(tmpl_data)
        stored = db["menu_templates"].find_one({"_id": __import__("bson").ObjectId(new_id)})
        assert stored["i18n"]["locales"] == ["es-ES", "en-GB", "eu-ES"]


@pytest.mark.integration
class TestPublishTemplate:
    """
    Tests de `publish(template_id, notes)`.
    """

    def test_returns_none_when_template_not_found(self, db):
        from bson import ObjectId
        assert _svc(db).publish(str(ObjectId())) is None

    def test_publishes_draft_template_successfully(self, db):
        tmpl = seed_template(db, slug="x", version=1, status="draft")
        result = _svc(db).publish(str(tmpl["_id"]))
        assert result == str(tmpl["_id"])
        # Verificar en DB.
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert stored["status"] == "published"

    def test_increments_version_when_republishing_published_template(self, db):
        tmpl = seed_template(db, slug="repub", version=1, status="published")
        result = _svc(db).publish(str(tmpl["_id"]))
        # Debe devolver el ID de un NUEVO documento (no el original).
        assert isinstance(result, str)
        assert result != str(tmpl["_id"])
        # En DB ahora hay dos documentos con el mismo slug.
        docs = list(db["menu_templates"].find({"slug": "repub"}))
        assert len(docs) == 2
        versions = sorted([d["version"] for d in docs])
        assert versions == [1, 2]

    def test_does_not_mutate_existing_published_doc(self, db):
        tmpl = seed_template(db, slug="immutable", version=1, status="published")
        _svc(db).publish(str(tmpl["_id"]))
        from bson import ObjectId
        original = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert original["version"] == 1
        assert original["status"] == "published"


@pytest.mark.integration
class TestDuplicateTemplate:
    """Tests de `duplicate(template_id, slug, name)`."""

    def test_returns_none_when_template_not_found(self, db):
        from bson import ObjectId
        assert _svc(db).duplicate(str(ObjectId())) is None

    def test_duplicates_with_derived_slug_and_draft_status(self, db):
        tmpl = seed_template(db, slug="carta", version=3, status="published", name="Carta")
        new_id = _svc(db).duplicate(str(tmpl["_id"]))
        assert isinstance(new_id, str)
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(new_id)})
        assert stored["slug"] == "carta-copy"
        assert stored["version"] == 1
        assert stored["status"] == "draft"
        assert stored["name"] == "Carta (copia)"
        assert stored["publish_notes"] == ""

    def test_copies_sections_structure(self, db):
        tmpl = seed_template(db, slug="conseccs", version=1)
        new_id = _svc(db).duplicate(str(tmpl["_id"]))
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(new_id)})
        assert stored["sections"] == tmpl["sections"]

    def test_derives_incremental_slug_on_collision(self, db):
        tmpl = seed_template(db, slug="menu", version=1)
        seed_template(db, slug="menu-copy", version=1)
        seed_template(db, slug="menu-copy-2", version=1)
        new_id = _svc(db).duplicate(str(tmpl["_id"]))
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(new_id)})
        assert stored["slug"] == "menu-copy-3"

    def test_uses_explicit_slug_when_provided(self, db):
        tmpl = seed_template(db, slug="base", version=1)
        new_id = _svc(db).duplicate(str(tmpl["_id"]), slug="mi-nuevo-slug")
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(new_id)})
        assert stored["slug"] == "mi-nuevo-slug"

    def test_returns_conflict_when_explicit_slug_exists(self, db):
        tmpl = seed_template(db, slug="base", version=1)
        seed_template(db, slug="ocupado", version=1)
        result = _svc(db).duplicate(str(tmpl["_id"]), slug="ocupado")
        assert isinstance(result, dict)
        assert "conflict" in result

    def test_does_not_mutate_original(self, db):
        tmpl = seed_template(db, slug="inmutable", version=2, status="published")
        _svc(db).duplicate(str(tmpl["_id"]))
        from bson import ObjectId
        original = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert original["version"] == 2
        assert original["status"] == "published"
        assert original["slug"] == "inmutable"


@pytest.mark.integration
class TestListTemplates:
    """
    Tests de `list(status, slug, tenant_id, skip, limit)`.
    """

    def test_returns_paginated_structure_with_items_and_total(self, db):
        seed_template(db, slug="a", version=1)
        seed_template(db, slug="b", version=1)
        result = _svc(db).list()
        assert set(result.keys()) == {"items", "total", "skip", "limit"}
        assert result["total"] == 2

    def test_filters_by_status(self, db):
        seed_template(db, slug="d", version=1, status="draft")
        seed_template(db, slug="p", version=1, status="published")
        result = _svc(db).list(status="draft")
        slugs = [t["slug"] for t in result["items"]]
        assert slugs == ["d"]

    def test_filters_by_tenant_id(self, db):
        seed_template(db, slug="ours", tenant_id="aralar")
        seed_template(db, slug="theirs", tenant_id="otro-tenant")
        result = _svc(db).list(tenant_id="aralar")
        slugs = [t["slug"] for t in result["items"]]
        assert slugs == ["ours"]


@pytest.mark.integration
class TestGetTemplateBySlugVersion:
    """
    Tests del lookup `repo.get_by_slug_version(slug, version)` que el service
    usa internamente al validar duplicados.
    """

    def test_returns_template_matching_slug_and_version(self, db):
        seed_template(db, slug="findme", version=2)
        repo = MenuTemplatesRepo(db)
        found = repo.get_by_slug_version("findme", 2)
        assert found is not None
        assert found["slug"] == "findme"
        assert found["version"] == 2

    def test_returns_none_when_combination_not_found(self, db):
        seed_template(db, slug="exists", version=1)
        repo = MenuTemplatesRepo(db)
        assert repo.get_by_slug_version("exists", 999) is None


@pytest.mark.integration
class TestUpdateDraft:
    """
    Tests de `update_draft(template_id, patch)`.
    Solo se permite editar templates en estado `draft`.
    """

    def test_updates_draft_template_successfully(self, db):
        tmpl = seed_template(db, slug="editable", status="draft", name="Original")
        result = _svc(db).update_draft(str(tmpl["_id"]), {"name": "Cambiado"})
        assert result == str(tmpl["_id"])
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert stored["name"] == "Cambiado"

    def test_returns_conflict_when_template_is_published(self, db):
        tmpl = seed_template(db, slug="locked", status="published")
        result = _svc(db).update_draft(str(tmpl["_id"]), {"name": "No funciona"})
        assert isinstance(result, dict)
        assert "conflict" in result

    def test_returns_none_when_template_not_found(self, db):
        from bson import ObjectId
        assert _svc(db).update_draft(str(ObjectId()), {"name": "x"}) is None

    def test_ignores_identity_fields(self, db):
        """slug/version/tenant_id/status son identidad y se descartan.

        Cambiar el slug dejaría huérfanos a los menús que apuntan a
        (template_slug, template_version): perderían el `ui` en /render y
        `delete_template` dejaría de contarlos.
        """
        tmpl = seed_template(db, slug="estable", version=1, status="draft", name="Original")
        result = _svc(db).update_draft(str(tmpl["_id"]), {
            "name": "Cambiado", "slug": "otro", "version": 99,
            "tenant_id": "otro-tenant", "status": "published",
        })
        assert result == str(tmpl["_id"])

        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert stored["name"] == "Cambiado"        # lo editable sí cambia
        assert stored["slug"] == "estable"          # la identidad no
        assert stored["version"] == 1
        assert stored["tenant_id"] == "aralar"
        assert stored["status"] == "draft"

    def test_slug_stays_immutable_after_unpublish(self, db):
        """Ruta adversarial: publicar → unpublish (vuelve a draft) → renombrar.

        `unpublish` reabre la ventana de edición, así que la inmutabilidad del
        slug tiene que vivir en el service, no solo en el estado del template.
        """
        tmpl = seed_template(db, slug="estable", version=1, status="published")
        svc = _svc(db)
        svc.unpublish(str(tmpl["_id"]))
        svc.update_draft(str(tmpl["_id"]), {"name": "X", "slug": "renombrado"})

        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert stored["slug"] == "estable"


@pytest.mark.integration
class TestUnpublish:
    """Tests de `unpublish(template_id)`."""

    def test_returns_none_when_template_not_found(self, db):
        from bson import ObjectId
        assert _svc(db).unpublish(str(ObjectId())) is None

    def test_returns_conflict_when_template_is_draft(self, db):
        tmpl = seed_template(db, status="draft")
        result = _svc(db).unpublish(str(tmpl["_id"]))
        assert isinstance(result, dict)
        assert "conflict" in result

    def test_returns_template_id_and_sets_status_to_draft(self, db):
        tmpl = seed_template(db, status="published")
        result = _svc(db).unpublish(str(tmpl["_id"]))
        assert result == str(tmpl["_id"])
        from bson import ObjectId
        stored = db["menu_templates"].find_one({"_id": ObjectId(str(tmpl["_id"]))})
        assert stored["status"] == "draft"


@pytest.mark.integration
class TestDeleteTemplate:
    """
    Tests de `delete_template(template_id, menus_repo)`.
    Rechaza el borrado si hay menús usando ese template.
    """

    def test_returns_none_when_template_not_found(self, db):
        from bson import ObjectId
        result = _svc(db).delete_template(str(ObjectId()), MenusRepo(db))
        assert result is None

    def test_returns_conflict_when_menus_use_template(self, db):
        tmpl = seed_template(db, slug="usado", version=1)
        seed_menu(db, template_slug="usado", template_version=1)
        result = _svc(db).delete_template(str(tmpl["_id"]), MenusRepo(db))
        assert isinstance(result, dict)
        assert "conflict" in result

    def test_deletes_template_when_no_menus_use_it(self, db):
        tmpl = seed_template(db, slug="huerfano", version=1)
        result = _svc(db).delete_template(str(tmpl["_id"]), MenusRepo(db))
        assert result == str(tmpl["_id"])
        assert db["menu_templates"].count_documents({"slug": "huerfano"}) == 0
