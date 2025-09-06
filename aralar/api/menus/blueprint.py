from flask_smorest import Blueprint
from flask import request, current_app, jsonify, make_response
from marshmallow import ValidationError
from ...repositories.menus_repo import MenusRepo
from ...services.menus_service import MenusService
from ...schemas.menu_availability_schemas import AvailabilitySchema
from ...schemas.menu_schemas import MenuCreateSchema, MenuCommonUpdateSchema, MenuLocaleUpdateSchema
from ...core.security import require_permissions

blp = Blueprint("menus", "menus", description="Menus endpoints")

availability_schema = AvailabilitySchema()

def get_svc():
    # Usa la DB inicializada en init_extensions(app)
    db = current_app.mongo_db
    return MenusService(MenusRepo(db))


@blp.route("", methods=["POST"])
@require_permissions("menus:create")
def create_menu():
    svc = get_svc()
    try:
        data = MenuCreateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    doc = svc.create(data)
    if not doc:
        return make_response(jsonify({"message": "template not found"}), 400)
    return make_response(jsonify(doc), 201)


@blp.route("", methods=["GET"])
@require_permissions("menus:read")
def list_menus():
    svc = get_svc()
    f = {}
    for k in ("status", "tenant_id", "template_slug", "template_version"):
        v = request.args.get(k)
        if v is not None:
            f[k] = int(v) if k == "template_version" else v
    items = svc.list(f)
    return make_response(jsonify({"items": items}), 200)


@blp.route("/<menu_id>", methods=["GET"])
@require_permissions("menus:read")
def get_menu(menu_id):
    svc = get_svc()
    doc = svc.get(menu_id)
    if not doc:
        return make_response(jsonify({"message": "not found"}), 404)
    return make_response(jsonify(doc), 200)


@blp.route("/<menu_id>/common", methods=["PUT"])
@require_permissions("menus:update")
def update_menu_common(menu_id):
    svc = get_svc()
    try:
        body = MenuCommonUpdateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    doc = svc.update_common(menu_id, body["common"])
    if not doc:
        return make_response(jsonify({"message": "not found"}), 404)
    return make_response(jsonify({"message": "ok"}), 200)


@blp.route("/<menu_id>/locales/<locale>", methods=["PUT"])
@require_permissions("menus:update")
def update_menu_locale(menu_id, locale):
    svc = get_svc()
    try:
        body = MenuLocaleUpdateSchema().load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    doc = svc.update_locale(menu_id, locale, body["data"])
    if not doc:
        return make_response(jsonify({"message": "not found"}), 404)
    return make_response(jsonify({"message": "ok"}), 200)


@blp.route("/<menu_id>/publish/<locale>", methods=["POST"])
@require_permissions("menus:publish")
def publish_menu_locale(menu_id, locale):
    svc = get_svc()
    doc = svc.publish_locale(menu_id, locale)
    if not doc:
        return make_response(jsonify({"message": "not found"}), 404)
    return make_response(jsonify({"message": "ok"}), 200)


@blp.route("/<menu_id>/archive", methods=["POST"])
@require_permissions("menus:archive")
def archive_menu(menu_id):
    svc = get_svc()
    m = svc.get(menu_id)
    if not m:
        return make_response(jsonify({"message": "not found"}), 404)
    if m.get("status") == "archived":
        return make_response(jsonify({"message": "already archived"}), 200)
    svc.repo.update(menu_id, {"status": "archived"})
    return make_response(jsonify({"message": "ok"}), 200)


@blp.route("/<menu_id>/availability", methods=["PUT"])
@require_permissions("menus:update")
def set_menu_availability(menu_id):
    svc = get_svc()
    try:
        payload = availability_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    doc = svc.set_availability(menu_id, payload)
    if not doc:
        return make_response(jsonify({"message": "menu not found"}), 404)
    return make_response(jsonify({"message": "ok"}), 200)


@blp.route("/public/available", methods=["GET"])
def public_available():
    """
    Params:
      - locale=es-ES (requerido)
      - date=YYYY-MM-DD (opcional; si no se pasa, usa 'ahora' con tz)
      - tz=Europe/Madrid (recomendado; default = Europe/Madrid)
    """
    locale = request.args.get("locale")
    tzname = request.args.get("tz", "Europe/Madrid")
    date_str = request.args.get("date", None)
    if not locale:
        return {"message": "locale is required"}, 400

    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    if date_str:
        try:
            # interpretamos medianoche local del tz dado
            dt_local = datetime.fromisoformat(date_str)
            if dt_local.tzinfo is None:
                dt_local = dt_local.replace(tzinfo=ZoneInfo(tzname))
            dt_utc = dt_local.astimezone(timezone.utc)
        except Exception:
            return {"message": "invalid date"}, 400
        items = svc.available_on(locale=locale, tzname=tzname, date_utc=dt_utc)
    else:
        items = svc.active_now(locale=locale, tzname=tzname)

    # Devuelve metadatos mínimos; tu endpoint /render usará el _id de aquí
    return {
        "items": [
            {
                "id": str(x["_id"]),
                "template_slug": x.get("template_slug"),
                "template_version": x.get("template_version"),
                "updated_at": x.get("updated_at"),
            }
            for x in items
        ]
    }, 200
