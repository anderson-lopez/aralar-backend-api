from flask_smorest import Blueprint, abort
from flask import current_app, request
from bson import ObjectId
from ...repositories.menus_repo import MenusRepo
from ...repositories.menu_templates_repo import MenuTemplatesRepo
from ...services.menus_service import MenusService
from ...schemas.menu_availability_schemas import AvailabilitySchema
from ...schemas.menu_schemas import (
    MenuCreateSchema,
    MenuCommonUpdateSchema,
    MenuLocaleUpdateSchema,
    MenuSchema,
    MenuListSchema,
    MenuListQueryArgs,
    MenuMessageSchema,
    PublicAvailableQueryArgs,
    MenuPublicAvailableListSchema,
    RenderQueryArgs,
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
    return MenusService(MenusRepo(db), MenuTemplatesRepo(db))


@blp.route("", methods=["POST"])
@require_permissions("menus:create")
@blp.arguments(MenuCreateSchema)
@blp.response(201, MenuSchema)
@blp.alt_response(400, schema=MenuMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def create_menu(data):
    svc = get_svc()
    doc = svc.create(data)
    if not doc:
        abort(400, message="template not found")
    return doc


@blp.route("", methods=["GET"])
@require_permissions("menus:read")
@blp.arguments(MenuListQueryArgs, location="query")
@blp.response(200, MenuListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_menus(query_args):
    svc = get_svc()
    items = svc.list(query_args)
    return {"items": items}


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
@blp.doc(security=[{"bearerAuth": []}])
def publish_menu_locale(menu_id, locale):
    svc = get_svc()
    doc = svc.publish_locale(menu_id, locale)
    if not doc:
        abort(404, message="not found")
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

    return {
        "items": [
            {
                "id": str(x.get("_id")),
                "template_slug": x.get("template_slug"),
                "template_version": x.get("template_version"),
                "updated_at": x.get("updated_at"),
                "title": svc.resolve_meta(x, "title", locale, fallback),
                "summary": svc.resolve_meta(x, "summary", locale, fallback),
            }
            for x in items
        ]
    }


@blp.route("/<menu_id>/render", methods=["GET"])
@blp.arguments(RenderQueryArgs, location="query")
@blp.alt_response(400, schema=MenuMessageSchema, description="Invalid id or params")
def render_menu(query, menu_id):
    """
    Devuelve el JSON final fusionado para ser mostrado en el frontend público.

    Query:
      - locale=es-ES   (requerido)
      - fallback=en-GB (opcional) => si no hay traducción en 'locale', usa esta
    """
    _abort_if_invalid_id(menu_id)
    locale = query.get("locale")
    fallback = query.get("fallback")
    include_ui = request.args.get("with_ui") in ("1", "true", "yes")  # <<--- NUEVO
    if not locale:
        abort(400, message="locale is required")

    svc = get_svc()
    payload = svc.render(menu_id, locale=locale, fallback=fallback, include_ui=include_ui)
    return payload
