from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from flask_smorest import abort


def compute_effective_permissions(user_doc, resolved_roles):
    role_perms = {p for r in resolved_roles for p in r.get("permissions", [])}
    allow = set(user_doc.get("permissions_allow", []) or [])
    deny = set(user_doc.get("permissions_deny", []) or [])
    eff = (role_perms | allow) - deny
    return sorted(eff)


def _deny():
    # Use Flask-Smorest abort to ensure a consistent JSON error body even with @blp.response wrappers
    abort(403, message="forbidden")


def require_roles(*roles):
    """Permite solo si el usuario tiene TODOS esos roles."""
    roles = set(roles)

    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
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
            claims = get_jwt()
            user_perms = set(claims.get("permissions", []))
            if not (user_perms & perms):
                return _deny()
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
