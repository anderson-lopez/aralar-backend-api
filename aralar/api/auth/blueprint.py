from flask_smorest import Blueprint
from flask import request
from datetime import timedelta
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from ...extensions import limiter
from ...repositories.users_repo import UsersRepo
from ...repositories.roles_repo import RolesRepo
from ...services.users_service import UsersService
from ...services.auth_service import AuthService
from ...core.security import jwt_claims_from_user
from ...schemas.auth_schemas import (
    LoginSchema,
    LoginResponseSchema,
    AuthErrorSchema,
    UserInfoSchema,
    RegisterSchema,
    RegisterResponseSchema,
    ChangePasswordSchema,
    ChangePasswordResponseSchema,
)
from flask import current_app
from flask_smorest import abort

blp = Blueprint("auth", "auth", description="Auth endpoints")


@blp.route("/login", methods=["POST"])
@blp.arguments(LoginSchema)
@blp.response(200, LoginResponseSchema)
@blp.alt_response(400, schema=AuthErrorSchema)
@blp.alt_response(401, schema=AuthErrorSchema)
@limiter.limit("5/minute")  # frena fuerza bruta
def login(login_data):
    """Authenticate user and return JWT tokens"""
    users_svc = UsersService(UsersRepo(current_app.mongo_db))
    roles_repo = RolesRepo(current_app.mongo_db)

    user = users_svc.verify_credentials(login_data["email"], login_data["password"])
    print("1")
    print(user)
    if not user:
        abort(401, message="Invalid email or password", error="authentication_failed")

    resolved_roles = roles_repo.resolve_roles(user.get("roles", []))
    claims = jwt_claims_from_user(user, resolved_roles=resolved_roles)

    return {
        "access_token": create_access_token(
            identity=str(user["_id"]),
            additional_claims=claims,
            expires_delta=timedelta(minutes=180),
        ),
        "refresh_token": create_refresh_token(identity=str(user["_id"]), additional_claims=claims),
    }


@blp.route("/me", methods=["GET"])
@blp.response(200, UserInfoSchema)
@blp.alt_response(401, schema=AuthErrorSchema)
@blp.doc(security=[{"bearerAuth": []}])
@jwt_required()
def me():
    """Get current user information from JWT token"""
    from flask_jwt_extended import get_jwt_identity, get_jwt

    # Obtener claims del JWT
    claims = get_jwt()
    user_id = get_jwt_identity()

    # Retornar información del usuario desde los claims
    return {
        "user_id": user_id,
        "email": claims.get("email"),
        "roles": claims.get("roles", []),
        "permissions": claims.get("permissions", []),
    }


@blp.route("/register", methods=["POST"])
@blp.arguments(RegisterSchema)
@blp.response(201, RegisterResponseSchema)
@blp.alt_response(400, schema=AuthErrorSchema)
@blp.alt_response(401, schema=AuthErrorSchema)
def register(register_data):
    """Register a new user"""
    try:
        users_svc = UsersService(UsersRepo(current_app.mongo_db))
        auth_svc = AuthService(users_svc)
        user_id = auth_svc.register(register_data)

        return {"message": "User registered successfully", "user_id": str(user_id)}
    except ValueError as e:
        abort(400, message=str(e), error="validation_error")
    except Exception as e:
        abort(400, message="Registration failed", error="registration_error")


@blp.route("/change-password", methods=["PUT"])
@blp.arguments(ChangePasswordSchema)
@blp.response(200, ChangePasswordResponseSchema)
@blp.alt_response(400, schema=AuthErrorSchema)
@blp.alt_response(401, schema=AuthErrorSchema)
@blp.doc(security=[{"bearerAuth": []}])
@jwt_required()
def change_password(change_password_data):
    """Change user password"""
    from flask_jwt_extended import get_jwt_identity, get_jwt

    # Obtener claims del JWT
    claims = get_jwt()
    user_id = get_jwt_identity()

    try:
        users_svc = UsersService(UsersRepo(current_app.mongo_db))
        users_svc.change_password(user_id, change_password_data)

        return {"message": "Password changed successfully"}
    except ValueError as e:
        abort(400, message=str(e), error="validation_error")
    except Exception as e:
        abort(400, message="Password change failed", error="password_change_error")
