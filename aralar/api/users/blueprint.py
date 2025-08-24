from flask_smorest import Blueprint
from ...repositories.users_repo import UsersRepo
from ...services.users_service import UsersService
from ...schemas.user_schemas import (
    UserCreateSchema,
    UserOutSchema,
    UserPermsUpdateSchema,
    UserRolesUpdateSchema,
    UserCreateResponseSchema,
    UserListResponseSchema,
)
from ...core.security import require_permissions
from ...core.validators import validate_object_id
from marshmallow import ValidationError
from flask import current_app

blp = Blueprint("users", "users", description="Users endpoints")

create_schema = UserCreateSchema()
out_schema = UserOutSchema()


@blp.route("", methods=["POST"])
@blp.arguments(UserCreateSchema)
@blp.response(201, UserCreateResponseSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:create")
def create_user(user_data):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    user_id = svc.create_user(user_data)
    return {"id": user_id}, 201


@blp.route("", methods=["GET"])
@blp.response(200, UserListResponseSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:read")
def list_users():
    svc = UsersService(UsersRepo(current_app.mongo_db))
    docs = svc.repo.list(limit=50)
    return {"items": docs}, 200


@blp.route("/<user_id>", methods=["GET"])
@blp.response(200, UserOutSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:read")
@validate_object_id("user_id")
def get_user(user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    doc = svc.repo.find_by_id(user_id)
    if not doc:
        return {"error": "User not found"}, 404
    return doc, 200


@blp.route("/<user_id>/permissions", methods=["PUT"])
@blp.arguments(UserPermsUpdateSchema)
@blp.response(200, UserOutSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:assign_permissions")
@validate_object_id("user_id")
def update_user_permissions(permissions_data, user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    svc.repo.set_user_permissions(
        user_id, permissions_data["permissions_allow"], permissions_data["permissions_deny"]
    )
    doc = svc.repo.find_by_id(user_id)
    return doc, 200


@blp.route("/<user_id>/roles", methods=["PUT"])
@blp.arguments(UserRolesUpdateSchema)
@blp.response(200, UserOutSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:assign_roles")
@validate_object_id("user_id")
def update_user_roles(roles_data, user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    svc.repo.set_user_roles(user_id, roles_data["roles"])
    doc = svc.repo.find_by_id(user_id)
    return doc, 200


@blp.route("/<user_id>/activate", methods=["PUT"])
@blp.response(200, UserOutSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:activate")
@validate_object_id("user_id")
def activate_user(user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    doc = svc.repo.update(user_id, {"is_active": True})
    return doc, 200


@blp.route("/<user_id>/deactivate", methods=["PUT"])
@blp.response(200, UserOutSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:activate")
@validate_object_id("user_id")
def deactivate_user(user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    doc = svc.repo.update(user_id, {"is_active": False})
    return doc, 200
