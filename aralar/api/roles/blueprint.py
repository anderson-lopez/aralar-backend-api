from flask_smorest import Blueprint, abort
from flask import current_app
from ...repositories.roles_repo import RolesRepo
from ...services.roles_service import RolesService
from ...schemas.role_schemas import (
    RoleSchema,
    RoleCreateUpdateSchema,
    RoleListSchema,
    PermissionSchema,
    PermissionUpsertSchema,
    PermissionListSchema,
    RoleMessageSchema,
)
from ...core.security import require_permissions


blp = Blueprint("roles", "roles", description="Roles management endpoints")


def get_svc():
    db = current_app.mongo_db
    return RolesService(RolesRepo(db))


@blp.route("", methods=["GET"])
@require_permissions("roles:read")
@blp.response(200, RoleListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_roles():
    svc = get_svc()
    items = svc.list_roles()
    return {"items": items}


@blp.route("", methods=["POST"])
@require_permissions("roles:create")
@blp.arguments(RoleCreateUpdateSchema)
@blp.response(201, RoleSchema)
@blp.alt_response(409, schema=RoleMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def create_role(body):
    svc = get_svc()
    if not body.get("name"):
        abort(400, message="name is required")
    res = svc.create_role(body)
    if isinstance(res, dict) and res.get("conflict"):
        abort(409, message=res["conflict"])
    return res


@blp.route("/<name>", methods=["GET"])
@require_permissions("roles:read")
@blp.response(200, RoleSchema)
@blp.alt_response(404, schema=RoleMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def get_role(name):
    svc = get_svc()
    doc = svc.get_role(name)
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<name>", methods=["PUT"])
@require_permissions("roles:update")
@blp.arguments(RoleCreateUpdateSchema)
@blp.response(200, RoleSchema)
@blp.alt_response(404, schema=RoleMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_role(name, body):
    svc = get_svc()
    doc = svc.update_role(name, body)
    if not doc:
        abort(404, message="not found")
    return doc


@blp.route("/<name>", methods=["DELETE"])
@require_permissions("roles:delete")
@blp.response(200, RoleMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def delete_role(name):
    svc = get_svc()
    deleted = svc.delete_role(name)
    if deleted == 0:
        return {"message": "not found"}
    return {"message": "ok"}


@blp.route("/permissions", methods=["GET"])
@require_permissions("roles:permissions:read")
@blp.response(200, PermissionListSchema)
@blp.doc(security=[{"bearerAuth": []}])
def list_permissions():
    svc = get_svc()
    items = svc.list_permissions()
    return {"items": items}


@blp.route("/permissions/<name>", methods=["PUT"])
@require_permissions("roles:permissions:update")
@blp.arguments(PermissionUpsertSchema)
@blp.response(200, PermissionSchema)
@blp.doc(security=[{"bearerAuth": []}])
def upsert_permission(body, name):
    svc = get_svc()
    doc = svc.upsert_permission(name, body)
    return doc


@blp.route("/permissions/id/<permission_id>", methods=["PUT"])
@require_permissions("roles:permissions:update")
@blp.arguments(PermissionUpsertSchema)
@blp.response(200, PermissionSchema)
@blp.alt_response(404, schema=RoleMessageSchema)
@blp.doc(security=[{"bearerAuth": []}])
def update_permission_by_id(body, permission_id):
    """Update permission description by ID (safer for names with special characters)"""
    svc = get_svc()
    doc = svc.update_permission_by_id(permission_id, body)
    if not doc:
        abort(404, message="Permission not found")
    return doc
