from flask_smorest import Blueprint, abort
from flask import current_app
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
    MessageSchema,
    PublicAvailableQueryArgs,
    MenuPublicAvailableListSchema,
)
from ...core.security import require_permissions

blp = Blueprint("menus", "menus", description="Menus endpoints")

def get_svc():
    # Usa la DB inicializada en init_extensions(app)
    db = current_app.mongo_db
    return MenusService(MenusRepo(db), MenuTemplatesRepo(db))


@blp.route("", methods=["POST"])
@require_permissions("menus:create")
@blp.arguments(MenuCreateSchema)
@blp.response(201, MenuSchema)
@blp.alt_response(400, schema=MessageSchema)
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
@blp.alt_response(404, schema=MessageSchema)
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
@blp.response(200, MessageSchema)
@blp.alt_response(404, schema=MessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_menu_common(menu_id, body):
    svc = get_svc()
    doc = svc.update_common(menu_id, body["common"])
    if not doc:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/locales/<locale>", methods=["PUT"])
@require_permissions("menus:update")
@blp.arguments(MenuLocaleUpdateSchema)
@blp.response(200, MessageSchema)
@blp.alt_response(404, schema=MessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_menu_locale(menu_id, locale, body):
    svc = get_svc()
    doc = svc.update_locale(menu_id, locale, body["data"])
    if not doc:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/publish/<locale>", methods=["POST"])
@require_permissions("menus:publish")
@blp.response(200, MessageSchema)
@blp.alt_response(404, schema=MessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def publish_menu_locale(menu_id, locale):
    svc = get_svc()
    doc = svc.publish_locale(menu_id, locale)
    if not doc:
        abort(404, message="not found")
    return {"message": "ok"}


@blp.route("/<menu_id>/archive", methods=["POST"])
@require_permissions("menus:archive")
@blp.response(200, MessageSchema)
@blp.alt_response(404, schema=MessageSchema)
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
@blp.response(200, MessageSchema)
@blp.alt_response(404, schema=MessageSchema)
@blp.alt_response(422, schema=MessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def set_menu_availability(menu_id, payload):
    svc = get_svc()
    doc = svc.set_availability(menu_id, payload)
    if not doc:
        abort(404, message="menu not found")
    return {"message": "ok"}


@blp.route("/public/available", methods=["GET"])
@blp.arguments(PublicAvailableQueryArgs, location="query")
@blp.response(200, MenuPublicAvailableListSchema)
@blp.alt_response(400, schema=MessageSchema)
def public_available(query):
    """List public menus available now or on a given date for a locale and tz."""
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    locale = query.get("locale")
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
            }
            for x in items
        ]
    }
