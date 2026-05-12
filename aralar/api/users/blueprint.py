from flask_smorest import Blueprint
from ...repositories.users_repo import UsersRepo
from ...services.users_service import UsersService
from ...schemas.user_schemas import (
    UserCreateSchema,
    UserCreateResponseSchema,
    UserOutSchema,
    UserListResponseSchema,
    UserUpdateSchema,
    UserPermsUpdateSchema,
    UserRolesUpdateSchema,
    UserDeleteResponseSchema,
    UserListQueryArgs,
)
from ...schemas.auth_schemas import ChangePasswordSchema
from ...core.security import require_permissions
from ...core.validators import validate_object_id
from marshmallow import ValidationError
from flask import current_app
from flask_jwt_extended import get_jwt_identity
from flask_smorest import abort

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
@blp.arguments(UserListQueryArgs, location="query")
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:read")
def list_users(query_args):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    result = svc.list_users(**query_args)
    return result, 200


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


@blp.route("/<user_id>", methods=["PUT"])
@blp.arguments(UserUpdateSchema)
@blp.response(200, UserOutSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:update")
@validate_object_id("user_id")
def update_user(user_data, user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    doc = svc.update_user(user_id, user_data)
    return doc, 200


@blp.route("/<user_id>", methods=["DELETE"])
@blp.response(200, UserDeleteResponseSchema)
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:delete")
@validate_object_id("user_id")
def delete_user(user_id):
    # Reglas anti-softlock:
    #   1) Nadie puede eliminarse a sí mismo.
    #   2) Nadie puede eliminar al ÚLTIMO admin activo (invariante: el
    #      sistema siempre debe tener >=1 admin activo).
    # El frontend deshabilita/oculta los botones; aquí va la defensa real.
    if str(get_jwt_identity()) == str(user_id):
        abort(400, message="No puedes eliminar tu propio usuario.")
    svc = UsersService(UsersRepo(current_app.mongo_db))
    if svc.is_last_active_admin(user_id):
        abort(400, message="No se puede eliminar al último admin activo del sistema.")
    svc.delete_user(user_id)
    return {"message": "User deleted successfully"}, 200


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
    new_roles = roles_data["roles"]
    # Si el target es el último admin activo y la nueva lista de roles le
    # quita 'admin', dejaríamos al sistema sin ningún admin operativo →
    # softlock. Se rechaza.
    if svc.is_last_active_admin(user_id) and "admin" not in new_roles:
        abort(
            400,
            message="No se puede quitar el rol admin al último admin activo del sistema.",
        )
    svc.repo.set_user_roles(user_id, new_roles)
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
    # Reglas anti-softlock (idénticas a delete):
    #   1) Nadie puede desactivarse a sí mismo.
    #   2) Nadie puede desactivar al último admin activo del sistema.
    if str(get_jwt_identity()) == str(user_id):
        abort(400, message="No puedes desactivar tu propio usuario.")
    svc = UsersService(UsersRepo(current_app.mongo_db))
    if svc.is_last_active_admin(user_id):
        abort(400, message="No se puede desactivar al último admin activo del sistema.")
    doc = svc.repo.update(user_id, {"is_active": False})
    return doc, 200


@blp.route("/<user_id>/change-password", methods=["PUT"])
@blp.arguments(ChangePasswordSchema)
@blp.response(200, {"message": "Password changed successfully"})
@blp.doc(security=[{"bearerAuth": []}])
@require_permissions("users:change_password")
@validate_object_id("user_id")
def change_password(password_data, user_id):
    svc = UsersService(UsersRepo(current_app.mongo_db))
    svc.change_password(user_id, password_data)
    return {"message": "Password changed successfully"}, 200
