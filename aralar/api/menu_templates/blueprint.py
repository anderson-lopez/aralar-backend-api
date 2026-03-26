from flask_smorest import Blueprint, abort
from flask import current_app
from ...repositories.menu_templates_repo import MenuTemplatesRepo
from ...repositories.menus_repo import MenusRepo
from ...services.menu_templates_service import MenuTemplatesService
from ...schemas.menu_template_schemas import (
    MenuTemplateCreateSchema,
    MenuTemplateUpdateSchema,
    MenuTemplatePublishSchema,
    MenuTemplateSchema,
    MenuTemplateListSchema,
    MenuTemplateQueryArgs,
    IdSchema,
    MenuTemplateMessageSchema,
)
from ...core.security import require_permissions

blp = Blueprint(
    "menu_templates",
    "menu_templates",
    url_prefix="/api/menu-templates",
    description="Menu Templates",
)


def get_svc():
    db = current_app.mongo_db
    return MenuTemplatesService(MenuTemplatesRepo(db))


@blp.route("", methods=["POST"])
@require_permissions("menu_templates:create")
@blp.arguments(MenuTemplateCreateSchema)
@blp.response(201, IdSchema)
@blp.alt_response(
    409,
    schema=MenuTemplateMessageSchema,
    description="Template with same slug and version already exists",
)
@blp.alt_response(422, schema=MenuTemplateMessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def create_template(data):
    """Create a new menu template (draft by default)"""
    svc = get_svc()
    result = svc.create(data)

    # Manejar caso de conflicto
    if isinstance(result, dict) and "conflict" in result:
        abort(409, description=result["conflict"])

    return {"id": result}


@blp.route("", methods=["GET"])
@require_permissions("menu_templates:read")
@blp.arguments(MenuTemplateQueryArgs, location="query")
@blp.response(200, MenuTemplateListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_templates(query_args):
    """List templates filtered by optional status, slug, and tenant_id"""
    svc = get_svc()
    result = svc.list(**query_args)
    return result


@blp.route("/<template_id>", methods=["GET"])
@require_permissions("menu_templates:read")
@blp.response(200, MenuTemplateSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def get_template(template_id):
    svc = get_svc()
    doc = svc.get(template_id)
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<template_id>", methods=["PUT"])
@require_permissions("menu_templates:update")
@blp.arguments(MenuTemplateUpdateSchema)
@blp.response(200, MenuTemplateMessageSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.alt_response(409, schema=MenuTemplateMessageSchema)
@blp.alt_response(422, schema=MenuTemplateMessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def update_template(patch, template_id):
    svc = get_svc()
    result = svc.update_draft(template_id, patch)
    if result is None:
        abort(404, message="not found")
    if isinstance(result, dict) and result.get("conflict"):
        abort(409, message=result["conflict"])
    return {"message": "ok"}


@blp.route("/<template_id>/publish", methods=["POST"])
@require_permissions("menu_templates:publish")
@blp.arguments(MenuTemplatePublishSchema)
@blp.response(201, IdSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.alt_response(422, schema=MenuTemplateMessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def publish_template(body, template_id):
    svc = get_svc()
    new_id = svc.publish(template_id, notes=body.get("notes"))
    if not new_id:
        abort(404, message="not found")
    return {"id": new_id}


@blp.route("/<template_id>/archive", methods=["POST"])
@require_permissions("menu_templates:archive")
@blp.response(200, MenuTemplateMessageSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def archive_template(template_id):
    svc = get_svc()
    doc = svc.get(template_id)
    if not doc:
        abort(404, message="not found")
    if doc.get("status") == "archived":
        return {"message": "already archived"}
    svc.repo.update(template_id, {"status": "archived"})
    return {"message": "ok"}


@blp.route("/<template_id>/unpublish", methods=["POST"])
@require_permissions("menu_templates:publish")
@blp.response(200, MenuTemplateMessageSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.alt_response(409, schema=MenuTemplateMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def unpublish_template(template_id):
    """Move a published template back to draft status"""
    svc = get_svc()
    result = svc.unpublish(template_id)
    if result is None:
        abort(404, message="not found")
    if isinstance(result, dict) and result.get("conflict"):
        abort(409, message=result["conflict"])
    return {"message": "ok"}


@blp.route("/<template_id>/unarchive", methods=["POST"])
@require_permissions("menu_templates:archive")
@blp.response(200, MenuTemplateMessageSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.alt_response(409, schema=MenuTemplateMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def unarchive_template(template_id):
    """Restore an archived template back to draft status"""
    svc = get_svc()
    result = svc.unarchive(template_id)
    if result is None:
        abort(404, message="not found")
    if isinstance(result, dict) and result.get("conflict"):
        abort(409, message=result["conflict"])
    return {"message": "ok"}


@blp.route("/<template_id>", methods=["DELETE"])
@require_permissions("menu_templates:delete")
@blp.response(200, MenuTemplateMessageSchema)
@blp.alt_response(404, schema=MenuTemplateMessageSchema)
@blp.alt_response(409, schema=MenuTemplateMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def delete_template(template_id):
    """Delete a template if no menus are using it"""
    svc = get_svc()
    menus_repo = MenusRepo(current_app.mongo_db)
    
    result = svc.delete_template(template_id, menus_repo)
    if result is None:
        abort(404, message="Template not found")
    if isinstance(result, dict) and result.get("conflict"):
        abort(409, message=result["conflict"])
    
    return {"message": "Template deleted successfully"}
