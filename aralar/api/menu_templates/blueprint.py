from flask_smorest import Blueprint
from flask import request, current_app, jsonify, make_response
from marshmallow import ValidationError
from ...repositories.menu_templates_repo import MenuTemplatesRepo
from ...services.menu_templates_service import MenuTemplatesService
from ...schemas.menu_template_schemas import (
    MenuTemplateCreateSchema,
    MenuTemplateUpdateSchema,
    MenuTemplatePublishSchema,
)
from ...core.security import require_permissions

blp = Blueprint(
    "menu_templates",
    "menu_templates",
    url_prefix="/api/menu-templates",
    description="Menu Templates",
)

create_schema = MenuTemplateCreateSchema()
update_schema = MenuTemplateUpdateSchema()
publish_schema = MenuTemplatePublishSchema()

def get_svc():
    db = current_app.mongo_db
    return MenuTemplatesService(MenuTemplatesRepo(db))


@blp.route("", methods=["POST"])
@require_permissions("menu_templates:create")
def create_template():
    svc = get_svc()
    try:
        data = create_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    _id = svc.create(data)
    return make_response(jsonify({"id": _id}), 201)


@blp.route("", methods=["GET"])
@require_permissions("menu_templates:read")
def list_templates():
    svc = get_svc()
    status = request.args.get("status")
    slug = request.args.get("slug")
    tenant_id = request.args.get("tenant_id")
    items = svc.list(status=status, slug=slug, tenant_id=tenant_id)
    return make_response(jsonify({"items": items}), 200)


@blp.route("/<template_id>", methods=["GET"])
@require_permissions("menu_templates:read")
def get_template(template_id):
    svc = get_svc()
    doc = svc.get(template_id)
    if not doc:
        return make_response(jsonify({"message": "not found"}), 404)
    return make_response(jsonify(doc), 200)


@blp.route("/<template_id>", methods=["PUT"])
@require_permissions("menu_templates:update")
def update_template(template_id):
    svc = get_svc()
    try:
        patch = update_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    result = svc.update_draft(template_id, patch)
    if result is None:
        return make_response(jsonify({"message": "not found"}), 404)
    if isinstance(result, dict) and result.get("conflict"):
        return make_response(jsonify({"message": result["conflict"]}), 409)
    return make_response(jsonify({"message": "ok"}), 200)


@blp.route("/<template_id>/publish", methods=["POST"])
@require_permissions("menu_templates:publish")
def publish_template(template_id):
    svc = get_svc()
    try:
        body = publish_schema.load(request.get_json() or {})
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages}), 400)
    new_id = svc.publish(template_id, notes=body.get("notes"))
    if not new_id:
        return make_response(jsonify({"message": "not found"}), 404)
    return make_response(jsonify({"id": new_id}), 201)


@blp.route("/<template_id>/archive", methods=["POST"])
@require_permissions("menu_templates:archive")
def archive_template(template_id):
    svc = get_svc()
    doc = svc.get(template_id)
    if not doc:
        return make_response(jsonify({"message": "not found"}), 404)
    if doc.get("status") == "archived":
        return make_response(jsonify({"message": "already archived"}), 200)
    svc.repo.update(template_id, {"status": "archived"})
    return make_response(jsonify({"message": "ok"}), 200)
