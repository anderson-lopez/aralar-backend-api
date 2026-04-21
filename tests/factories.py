"""
Factories: helpers para construir datos de prueba (menus, templates, users).

Usar factories en vez de escribir dicts gigantes en cada test evita duplicación
y deja los tests enfocados en el comportamiento que validan, no en el setup.

Patrón:
- Cada factory acepta **overrides como kwargs y devuelve un dict listo para
  insertar en mongomock (o enviar a un endpoint).
- Los defaults representan el caso más común/válido.
- El test sobreescribe SOLO los campos relevantes a lo que prueba.

Ejemplo:
    def test_menu_without_images_returns_empty_list():
        menu = make_menu(common={})
        assert MenusService(None, None).extract_image_urls(menu) == []

    def test_menu_with_banner_returns_one_image():
        menu = make_menu(common={
            "header": {"banner_image": {"url": "https://cdn/foo.jpg", "mime": "image/jpeg"}}
        })
        assert MenusService(None, None).extract_image_urls(menu) == ["https://cdn/foo.jpg"]
"""
from datetime import datetime, timezone
from typing import Optional


def make_menu(**overrides) -> dict:
    """
    Construye un documento de menú con defaults sensatos.

    Defaults:
    - status: "published"
    - template_slug: "test-template", template_version: 1
    - publish.es-ES.status: "published"
    - availability: todos los días, rango amplio 2020→2099
    - common + locales vacíos (sobrescribe si los necesitas)

    Override cualquier campo pasándolo como kwarg:
        make_menu(status="draft", name="Mi menú")
        make_menu(availability={"days_of_week": ["MON"], ...})
    """
    base = {
        "tenant_id": "aralar",
        "name": "Test Menu",
        "template_slug": "test-template",
        "template_version": 1,
        "status": "published",
        "featured": False,
        "featured_order": None,
        "common": {},
        "locales": {
            "es-ES": {
                "data": {},
                "meta": {"title": "Título ES", "summary": "Resumen ES"},
            }
        },
        "publish": {
            "es-ES": {"status": "published", "published_at": datetime.now(timezone.utc)},
        },
        "availability": {
            "timezone": "Europe/Madrid",
            "days_of_week": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
            "date_ranges": [{"start": "2020-01-01", "end": "2099-12-31"}],
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base


def make_template(**overrides) -> dict:
    """
    Construye un template publicado mínimo.

    Defaults:
    - slug: "test-template", version: 1, status: "published"
    - una sección 'items' repetible con campos _id, name
    """
    base = {
        "tenant_id": "aralar",
        "name": "Test Template",
        "slug": "test-template",
        "version": 1,
        "status": "published",
        "i18n": {"default_locale": "es-ES", "locales": ["es-ES", "en-GB"]},
        "sections": [
            {
                "key": "items",
                "label": {"es-ES": "Items", "en-GB": "Items"},
                "repeatable": True,
                "fields": [
                    {"key": "_id", "type": "text", "required": True, "translatable": False},
                    {"key": "name", "type": "text", "required": True, "translatable": True},
                ],
                "ui": {"role": "course_list", "order": 10, "display": "list"},
            }
        ],
        "ui": {"layout": "sections", "catalogs": {}},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base


def make_image(url: str = "https://cdn.example.com/test.webp",
               mime: str = "image/webp",
               width: int = 1200,
               height: int = 900,
               size: int = 180_000) -> dict:
    """
    Construye el dict de una imagen siguiendo el schema usado en todos los templates.

    Ejemplo:
        menu = make_menu(common={
            "dishes": [
                {"_id": "d1", "image": make_image(url="https://cdn/dish1.webp")},
                {"_id": "d2", "image": make_image(url="https://cdn/dish2.webp")},
            ]
        })
    """
    return {"url": url, "mime": mime, "width": width, "height": height, "size": size}


def seed_menu(db, **overrides) -> dict:
    """
    Inserta un menú en mongomock y devuelve el documento completo (con _id).

    Úsalo cuando el test necesite que el menú exista en la DB (tests E2E o
    de integración de service+repo).

    Ejemplo:
        def test_public_available_returns_seeded_menu(client, db):
            seed_menu(db, name="Menú de prueba")
            res = client.get("/api/menus/public/available?locale=es-ES")
            assert len(res.json["items"]) == 1
    """
    doc = make_menu(**overrides)
    inserted = db["menus"].insert_one(doc)
    doc["_id"] = inserted.inserted_id
    return doc


def seed_template(db, **overrides) -> dict:
    """Inserta un template en mongomock y devuelve el documento completo."""
    doc = make_template(**overrides)
    inserted = db["menu_templates"].insert_one(doc)
    doc["_id"] = inserted.inserted_id
    return doc
