from flask_smorest import Blueprint, abort
from flask import current_app, request
from bson import ObjectId
from ...repositories.menus_repo import MenusRepo
from ...repositories.menu_templates_repo import MenuTemplatesRepo
from ...repositories.menu_services_repo import MenuServicesRepo
from ...services.menus_service import MenusService
from ...schemas.menu_availability_schemas import AvailabilitySchema
from ...schemas.menu_schemas import (
    MenuCreateSchema,
    MenuDuplicateSchema,
    MenuCommonUpdateSchema,
    MenuGeneralUpdateSchema,
    MenuLocaleUpdateSchema,
    MenuSchema,
    MenuListSchema,
    MenuListQueryArgs,
    MenuMessageSchema,
    PublicAvailableQueryArgs,
    PublicFeaturedQueryArgs,
    MenuPublicAvailableListSchema,
    MenuFeaturedUpdateSchema,
    MenuFeaturedListSchema,
    RenderQueryArgs,
    RenderMultipleSchema,
    RenderMultipleResponseSchema,
)
from ...core.security import require_permissions

blp = Blueprint("menus", "menus", description="Menus endpoints")


def _abort_if_invalid_id(_id: str):
    try:
        ObjectId(_id)
    except Exception:
        abort(400, message="invalid id")


def get_svc():
    # Usa la DB inicializada en init_extensions(app)
    db = current_app.mongo_db
    return MenusService(MenusRepo(db), MenuTemplatesRepo(db), MenuServicesRepo(db))


def _public_item(svc, x, locale, fallback, images_limit):
    """Construye un item de listado público (MenuPublicItemSchema).

    Compartido por `/public/available` y `/public/services/<slug>`: mismas
    tarjetas ligeras (el frontend pide luego `/render`). `locale_used` indica el
    idioma efectivo para evitar el 409 por locale ausente.

    Devuelve `None` si el menú no tiene ningún idioma publicado: sin idioma no hay
    nada que mostrar ni forma de renderizarlo, así que se omite del listado en vez
    de devolver un `locale_used` inventado que reventaría al llamar a `/render`.
    """
    eff = svc.effective_locale(x, locale, fallback)
    if eff is None:
        return None
    return {
        "id": str(x.get("_id")),
        "name": x.get("name"),
        "template_slug": x.get("template_slug"),
        "template_version": x.get("template_version"),
        "updated_at": x.get("updated_at"),
        "list_order": x.get("list_order"),
        "service_slugs": x.get("service_slugs", []) or [],
        "locale_used": eff,
        "title": svc.resolve_meta(x, "title", eff, fallback),
        "summary": svc.resolve_meta(x, "summary", eff, fallback),
        "preview_images": svc.extract_image_urls(x, limit=images_limit),
    }


@blp.route("", methods=["POST"])
@require_permissions("menus:create")
@blp.arguments(MenuCreateSchema)
@blp.response(201, MenuSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def create_menu(data):
    svc = get_svc()
    doc = svc.create(data)
    if doc is None:
        abort(400, message="template not found")
    if isinstance(doc, dict) and doc.get("error"):
        abort(400, message=doc["error"])
    return doc


@blp.route("", methods=["GET"])
@require_permissions("menus:read")
@blp.arguments(MenuListQueryArgs, location="query")
@blp.response(200, MenuListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_menus(query_args):
    svc = get_svc()
    result = svc.list(query_args)
    return result


@blp.route("/<menu_id>/duplicate", methods=["POST"])
@require_permissions("menus:create")
@blp.arguments(MenuDuplicateSchema)
@blp.response(201, MenuSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def duplicate_menu(body, menu_id):
    """Duplica un menú existente como un nuevo draft.

    Copia common, locales y availability; resetea status a draft, limpia el
    estado de publicación y desmarca featured. Acepta un `name` opcional en el
    body; por defecto usa "<nombre> (copia)".
    """
    _abort_if_invalid_id(menu_id)
    svc = get_svc()
    doc = svc.duplicate(menu_id, name=body.get("name"))
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<menu_id>", methods=["GET"])
@require_permissions("menus:read")
@blp.response(200, MenuSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def get_menu(menu_id):
    svc = get_svc()
    doc = svc.get(menu_id)
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<menu_id>", methods=["DELETE"])
@require_permissions("menus:delete")
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def delete_menu(menu_id):
    """Elimina definitivamente un menú."""
    svc = get_svc()
    ok = svc.delete(menu_id)
    if not ok:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/common", methods=["PUT"])
@require_permissions("menus:update")
@blp.arguments(MenuCommonUpdateSchema)
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_menu_common(body, menu_id):
    svc = get_svc()
    doc = svc.update_common(menu_id, body["common"])
    if not doc:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/general", methods=["PUT"])
@require_permissions("menus:update")
@blp.arguments(MenuGeneralUpdateSchema)
@blp.response(200, MenuSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_menu_general(body, menu_id):
    svc = get_svc()
    doc = svc.update_general(menu_id, body)
    if doc is None:
        abort(404, message="not found")
    if isinstance(doc, dict) and doc.get("error"):
        abort(400, message=doc["error"])
    return doc


@blp.route("/<menu_id>/validate", methods=["GET"])
@require_permissions("menus:read")
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def validate_menu(menu_id):
    """Valida si el menú está listo para publicación global."""
    svc = get_svc()
    result = svc.validate_menu(menu_id)
    if result is None:
        abort(404, message="not found")
    # Reusamos MessageSchema para no crear otro schema: devolvemos un resumen
    # y adjuntamos issues en el payload (flask-smorest no lo impide aunque el schema sea simple)
    if result.get("ok"):
        return {"message": "ok"}
    # Cuando hay issues, devolvemos 200 con detalle en el cuerpo usando abort no es ideal,
    # así que retornamos un dict extendido; la UI debe leerlo.
    return {"message": "invalid", "issues": result.get("issues", [])}


@blp.route("/<menu_id>/publish", methods=["POST"])
@require_permissions("menus:publish")
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.alt_response(409, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def publish_menu(menu_id):
    svc = get_svc()
    result = svc.publish_menu(menu_id)
    if result is None:
        abort(404, message="not found")
    if not result.get("ok"):
        abort(409, message="; ".join(result.get("issues", [])))
    return {"message": "ok"}


@blp.route("/<menu_id>/unpublish", methods=["POST"])
@require_permissions("menus:publish")
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def unpublish_menu(menu_id):
    svc = get_svc()
    doc = svc.unpublish_menu(menu_id)
    if not doc:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/locales/<locale>", methods=["PUT"])
@require_permissions("menus:update")
@blp.arguments(MenuLocaleUpdateSchema)
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_menu_locale(body, menu_id, locale):
    svc = get_svc()
    doc = svc.update_locale(menu_id, locale, body["data"], body.get("meta"))
    if not doc:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/publish/<locale>", methods=["POST"])
@require_permissions("menus:publish")
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.alt_response(409, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def publish_menu_locale(menu_id, locale):
    """Publica un idioma del menú. 409 si ese idioma aún no tiene contenido."""
    svc = get_svc()
    doc = svc.publish_locale(menu_id, locale)
    if not doc:
        abort(404, message="not found")
    if isinstance(doc, dict) and doc.get("conflict"):
        abort(409, message=doc["conflict"])
    return {"message": "ok"}


@blp.route("/<menu_id>/archive", methods=["POST"])
@require_permissions("menus:archive")
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def archive_menu(menu_id):
    svc = get_svc()
    m = svc.get(menu_id)
    if not m:
        abort(404, message="not found")
    if m.get("status") == "archived":
        return {"message": "already archived"}
    svc.repo.update(menu_id, {"status": "archived"})
    return {"message": "ok"}


@blp.route("/<menu_id>/availability", methods=["PUT"])
@require_permissions("menus:update")
@blp.arguments(AvailabilitySchema)
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.alt_response(422, schema=MenuMessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def set_menu_availability(payload, menu_id):
    svc = get_svc()
    doc = svc.set_availability(menu_id, payload)
    if not doc:
        abort(404, message="menu not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/featured", methods=["PUT"])
@require_permissions("menus:update")
@blp.arguments(MenuFeaturedUpdateSchema)
@blp.response(200, MenuMessageSchema)
@blp.alt_response(404, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def set_menu_featured(payload, menu_id):
    """Update featured status and order of a menu"""
    svc = get_svc()
    doc = svc.update_featured(menu_id, payload["featured"], payload.get("featured_order"))
    if not doc:
        abort(404, message="menu not found")
    return {"message": "ok"}


@blp.route("/public/available", methods=["GET"])
@blp.arguments(PublicAvailableQueryArgs, location="query")
@blp.response(200, MenuPublicAvailableListSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
def public_available(query):
    """List public menus available now or on a given date for a locale and tz."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    locale = query.get("locale")
    fallback = query.get("fallback")
    tzname = query.get("tz") or "Europe/Madrid"
    date_str = query.get("date")
    images_limit = query.get("images_limit", 10)

    svc = get_svc()

    if date_str:
        try:
            dt_local = datetime.fromisoformat(date_str)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=ZoneInfo(tzname))
            dt_utc = dt_local.astimezone(timezone.utc)
        except Exception:
            abort(400, message="invalid date")
        items = svc.available_on(locale=locale, tzname=tzname, date_utc=dt_utc)
    else:
        items = svc.active_now(locale=locale, tzname=tzname)

    # `_public_item` devuelve None para menús sin ningún idioma publicado: se omiten.
    cards = (_public_item(svc, x, locale, fallback, images_limit) for x in items)
    return {"items": [c for c in cards if c is not None]}


@blp.route("/public/services/<service_slug>", methods=["GET"])
@blp.arguments(PublicAvailableQueryArgs, location="query")
@blp.response(200, MenuPublicAvailableListSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
def public_service_menus(query, service_slug):
    """Lista pública de menús clasificados en un servicio ("Otros servicios").

    Mismas tarjetas ligeras que `/public/available`; el frontend pide luego
    `/render` con `locale_used`. Estos menús NO aparecen en `/public/available`.
    """
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    locale = query.get("locale")
    fallback = query.get("fallback")
    tzname = query.get("tz") or "Europe/Madrid"
    date_str = query.get("date")
    images_limit = query.get("images_limit", 10)

    svc = get_svc()

    if date_str:
        try:
            dt_local = datetime.fromisoformat(date_str)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=ZoneInfo(tzname))
            dt_utc = dt_local.astimezone(timezone.utc)
        except Exception:
            abort(400, message="invalid date")
        items = svc.service_menus_on(service_slug, locale=locale, tzname=tzname, date_utc=dt_utc)
    else:
        items = svc.service_menus_now(service_slug, locale=locale, tzname=tzname)

    # `_public_item` devuelve None para menús sin ningún idioma publicado: se omiten.
    cards = (_public_item(svc, x, locale, fallback, images_limit) for x in items)
    return {"items": [c for c in cards if c is not None]}


@blp.route("/public/featured", methods=["GET"])
@blp.arguments(PublicFeaturedQueryArgs, location="query")
@blp.response(200, MenuFeaturedListSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
def public_featured(query):
    """List featured menus available now or on a given date, fully rendered for landing page."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    locale = query.get("locale")
    fallback = query.get("fallback")
    tzname = query.get("tz") or "Europe/Madrid"
    date_str = query.get("date")
    include_ui = query.get("include_ui", False)

    svc = get_svc()

    if date_str:
        try:
            dt_local = datetime.fromisoformat(date_str)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=ZoneInfo(tzname))
            dt_utc = dt_local.astimezone(timezone.utc)
        except Exception:
            abort(400, message="invalid date")
        items = svc.render_featured_menus(
            locale=locale, tzname=tzname, fallback=fallback, date_utc=dt_utc, include_ui=include_ui
        )
    else:
        items = svc.render_featured_menus(
            locale=locale, tzname=tzname, fallback=fallback, include_ui=include_ui
        )

    return {"items": items}


@blp.route("/render/multiple", methods=["POST"])
@blp.arguments(RenderMultipleSchema)
@blp.response(200, RenderMultipleResponseSchema)
@blp.alt_response(400, schema=MenuMessageSchema, description="Invalid request")
def render_multiple_menus(data):
    """
    Renderiza múltiples menus de una vez para optimizar requests del frontend.

    Útil cuando necesitas renderizar varios menus específicos (no necesariamente destacados).
    Máximo 10 menus por request para evitar timeouts.
    """
    svc = get_svc()

    # Validar que todos los IDs sean válidos
    for menu_id in data["menu_ids"]:
        _abort_if_invalid_id(menu_id)

    result = svc.render_multiple(
        menu_ids=data["menu_ids"],
        locale=data["locale"],
        fallback=data.get("fallback"),
        include_ui=data.get("include_ui", False),
    )

    return result


@blp.route("/<menu_id>/render", methods=["GET"])
@blp.arguments(RenderQueryArgs, location="query")
@blp.alt_response(400, schema=MenuMessageSchema, description="Invalid id or params")
def render_menu(query, menu_id):
    """
    Devuelve el JSON final fusionado para ser mostrado en el frontend público.

    Query:
      - locale=es-ES     (requerido)
      - fallback=en-GB   (opcional) => si no hay traducción en 'locale', usa esta
      - include_ui=true  (opcional) => incluir manifest de UI del template
    """
    _abort_if_invalid_id(menu_id)
    locale = query.get("locale")
    fallback = query.get("fallback")
    include_ui = query.get("include_ui", False)
    if not locale:
        abort(400, message="locale is required")

    svc = get_svc()
    payload = svc.render(menu_id, locale=locale, fallback=fallback, include_ui=include_ui)
    return payload
