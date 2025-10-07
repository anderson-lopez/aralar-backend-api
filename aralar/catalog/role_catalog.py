from __future__ import annotations

# Single source of truth for permissions and role templates
# Edit here to add/remove permissions or adjust role templates

DEFAULT_PERMISSIONS = [
    # usuarios
    "users:read",
    "users:create",
    "users:assign_roles",
    "users:assign_permissions", 
    "users:activate",
    # roles
    "roles:read",
    "roles:create",
    "roles:update",
    "roles:delete",
    "roles:permissions:read",
    "roles:permissions:update",
    # menus (incluye i18n y uploads)
    "menus:read",
    "menus:create",
    "menus:update",  # Usado también por i18n y uploads
    "menus:delete",
    "menus:publish",
    # menu templates
    "menu_templates:read",
    "menu_templates:create",
    "menu_templates:update",
    "menu_templates:publish",
    "menu_templates:archive",
    # auth admin
    "auth:invalidate_tokens",
    "auth:view_blacklist",
    # reservas (futuro)
    "reservas:read",
    "reservas:create",
    "reservas:update",
    "reservas:delete",
]

ROLE_TEMPLATES: dict[str, dict] = {
    "admin": {
        "description": "Administrador del sistema con todos los permisos",
        "permissions": DEFAULT_PERMISSIONS,
    },
    "manager": {
        "description": "Gestión operativa, alta/baja/edición excepto roles",
        "permissions": [
            "users:read",
            "users:update",
            "menus:read",
            "menus:create",
            "menus:update",
            "reservas:read",
            "reservas:create",
            "reservas:update",
        ],
    },
    "staff": {
        "description": "Personal, acceso mínimo",
        "permissions": ["menus:read", "reservas:read", "reservas:create"],
    },
    "user": {
        "description": "Usuario, acceso mínimo",
        "permissions": ["menus:read", "reservas:read", "reservas:create"],
    },
}


def apply_catalog(db):
    """Idempotently upsert permissions and role templates into the DB.

    - Ensures all permissions exist in collection `permissions`.
    - Ensures role documents exist/are updated in collection `roles` with sorted unique permissions.
    """
    # Permissions
    for p in DEFAULT_PERMISSIONS:
        db["permissions"].update_one({"name": p}, {"$set": {"description": ""}}, upsert=True)

    # Roles
    for name, data in ROLE_TEMPLATES.items():
        db["roles"].update_one(
            {"name": name},
            {
                "$set": {
                    "permissions": sorted(set(data["permissions"])),
                    "description": data["description"],
                }
            },
            upsert=True,
        )
