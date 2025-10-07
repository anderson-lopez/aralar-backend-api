from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from flask_smorest import abort
from flask import current_app


def compute_effective_permissions(user_doc, resolved_roles):
    role_perms = {p for r in resolved_roles for p in r.get("permissions", [])}
    allow = set(user_doc.get("permissions_allow", []) or [])
    deny = set(user_doc.get("permissions_deny", []) or [])
    eff = (role_perms | allow) - deny
    return sorted(eff)


def _deny():
    # Use Flask-Smorest abort to ensure a consistent JSON error body even with @blp.response wrappers
    abort(403, message="forbidden")


def _validate_token_version():
    """
    Valida que la versión de permisos del token coincida con la BD.
    Si no coincide, significa que los permisos/roles cambiaron y el token debe ser rechazado.
    """
    try:
        claims = get_jwt()
        user_id = get_jwt_identity()
        token_perm_v = claims.get("perm_v", 1)
        
        # Importar aquí para evitar circular imports
        from ..repositories.users_repo import UsersRepo
        
        users_repo = UsersRepo(current_app.mongo_db)
        user = users_repo.find_by_id(user_id)
        
        if not user:
            abort(401, message="User not found")
            
        # Verificar si el usuario está activo
        if not user.get("active", True):
            abort(401, message="User account is deactivated")
        
        # Verificar versión de permisos
        db_perm_v = user.get("perm_version", 1)
        if token_perm_v != db_perm_v:
            abort(401, message="Token expired due to permission changes. Please login again.")
            
    except Exception as e:
        # Si hay cualquier error en la validación, rechazar el token
        abort(401, message="Token validation failed")


def _validate_token_blacklist():
    """
    Valida que el token no esté en la blacklist.
    Si está blacklisted, significa que fue invalidado manualmente (logout, etc.).
    """
    try:
        claims = get_jwt()
        jti = claims.get("jti")
        
        if not jti:
            # Si no hay JTI, no podemos validar blacklist, pero permitimos continuar
            # Los tokens antiguos pueden no tener JTI
            return
        
        # Importar aquí para evitar circular imports
        from ..repositories.token_blacklist_repo import TokenBlacklistRepo
        
        blacklist_repo = TokenBlacklistRepo(current_app.mongo_db)
        
        if blacklist_repo.is_token_blacklisted(jti):
            abort(401, message="Token has been invalidated. Please login again.")
            
    except Exception as e:
        # Si hay cualquier error en la validación de blacklist, rechazar el token
        current_app.logger.error(f"Blacklist validation error: {str(e)}")
        abort(401, message="Token validation failed")


def require_roles(*roles):
    """Permite solo si el usuario tiene TODOS esos roles."""
    roles = set(roles)

    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            _validate_token_blacklist()  # ← Validar blacklist primero
            _validate_token_version()  # ← Validar versión antes de verificar permisos
            claims = get_jwt()
            user_roles = set(claims.get("roles", []))
            if not roles.issubset(user_roles):
                return _deny()
            return fn(*args, **kwargs)

        return decorated

    return wrapper


def require_any_role(*roles):
    """Permite si el usuario tiene AL MENOS uno de esos roles."""
    roles = set(roles)

    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            _validate_token_blacklist()  # ← Validar blacklist primero
            _validate_token_version()  # ← Validar versión antes de verificar permisos
            claims = get_jwt()
            user_roles = set(claims.get("roles", []))
            if not (user_roles & roles):
                return _deny()
            return fn(*args, **kwargs)

        return decorated

    return wrapper


def require_permissions(*permissions):
    """Permite solo si el usuario tiene TODOS esos permisos."""
    perms = set(permissions)

    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            _validate_token_blacklist()  # ← Validar blacklist primero
            _validate_token_version()  # ← Validar versión antes de verificar permisos
            claims = get_jwt()
            user_perms = set(claims.get("permissions", []))
            if not perms.issubset(user_perms):
                return _deny()
            return fn(*args, **kwargs)

        return decorated

    return wrapper


def require_any_permission(*permissions):
    """Permite si el usuario tiene AL MENOS uno de esos permisos."""
    perms = set(permissions)

    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            _validate_token_blacklist()  # ← Validar blacklist primero
            _validate_token_version()  # ← Validar versión antes de verificar permisos
            claims = get_jwt()
            user_perms = set(claims.get("permissions", []))
            if not (user_perms & perms):
                return _deny()
            return fn(*args, **kwargs)

        return decorated

    return wrapper


def jwt_required_with_version():
    """
    Decorador que combina @jwt_required() con validación de versión.
    Usar en lugar de @jwt_required() cuando quieras validar versiones.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            _validate_token_blacklist()  # ← Validar blacklist primero
            _validate_token_version()  # ← Validar versión del token
            return fn(*args, **kwargs)

        return decorated

    return wrapper


def jwt_claims_from_user(user_doc, resolved_roles=None):
    roles = user_doc.get("roles", [])
    email = user_doc.get("email")
    permissions = compute_effective_permissions(user_doc, resolved_roles or [])
    return {
        "sub": str(user_doc["_id"]),
        "roles": roles,
        "permissions": permissions,
        "email": email,
        # opcional: útil para invalidar tokens si cambian permisos
        "perm_v": int(user_doc.get("perm_version", 1)),
    }
