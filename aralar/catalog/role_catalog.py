from __future__ import annotations

# Single source of truth for permissions and role templates
# Edit here to add/remove permissions or adjust role templates

DEFAULT_PERMISSIONS: dict[str, str] = {
    # usuarios
    "users:read": "Ver listado y detalle de usuarios",
    "users:create": "Crear nuevos usuarios",
    "users:update": "Editar datos de perfil de usuarios",
    "users:delete": "Eliminar usuarios",
    "users:assign_roles": "Asignar roles a usuarios",
    "users:assign_permissions": "Asignar permisos directos a usuarios",
    "users:activate": "Activar o desactivar usuarios",
    "users:change_password": "Cambiar contraseña de otros usuarios",
    # roles
    "roles:read": "Ver listado y detalle de roles",
    "roles:create": "Crear nuevos roles",
    "roles:update": "Editar roles existentes",
    "roles:delete": "Eliminar roles",
    "roles:permissions:read": "Ver permisos asignados a roles",
    "roles:permissions:update": "Modificar permisos de roles",
    # menus (incluye i18n y uploads)
    "menus:read": "Ver menús",
    "menus:create": "Crear menús",
    "menus:update": "Editar menús, traducciones y archivos",
    "menus:delete": "Eliminar menús",
    "menus:archive": "Archivar menús",
    "menus:publish": "Publicar menús",
    # menu templates
    "menu_templates:read": "Ver plantillas de menú",
    "menu_templates:create": "Crear plantillas de menú",
    "menu_templates:update": "Editar plantillas de menú",
    "menu_templates:delete": "Eliminar plantillas de menú",
    "menu_templates:publish": "Publicar plantillas de menú",
    "menu_templates:archive": "Archivar plantillas de menú",
    # notifications
    "notifications:read": "Ver notificaciones",
    "notifications:create": "Crear notificaciones",
    "notifications:update": "Editar notificaciones",
    "notifications:delete": "Eliminar notificaciones",
    # auth admin
    "auth:invalidate_tokens": "Invalidar tokens de usuarios",
    "auth:view_blacklist": "Ver historial de tokens invalidados",
    # reservas (futuro)
    "reservas:read": "Ver reservas",
    "reservas:create": "Crear reservas",
    "reservas:update": "Editar reservas",
    "reservas:delete": "Eliminar reservas",
}

# Lista plana de nombres para compatibilidad con ROLE_TEMPLATES y otros usos
DEFAULT_PERMISSION_NAMES: list[str] = list(DEFAULT_PERMISSIONS.keys())

ROLE_TEMPLATES: dict[str, dict] = {
    "admin": {
        "description": "Administrador del sistema con todos los permisos",
        "permissions": DEFAULT_PERMISSION_NAMES,
    },
    "manager": {
        "description": "Gestión operativa, alta/baja/edición excepto roles",
        "permissions": [
            "users:read",
            "users:create",
            "users:update",
            "users:activate",
            "users:change_password",
            "menus:read",
            "menus:create",
            "menus:update",
            "notifications:read",
            "notifications:create",
            "notifications:update",
            "notifications:delete",
            "reservas:read",
            "reservas:create",
            "reservas:update",
        ],
    },
    "staff": {
        "description": "Personal, acceso mínimo",
        "permissions": ["menus:read", "notifications:read", "reservas:read", "reservas:create"],
    },
    "user": {
        "description": "Usuario, acceso mínimo",
        "permissions": ["menus:read", "notifications:read", "reservas:read", "reservas:create"],
    },
}


def apply_catalog(db):
    """Idempotently upsert permissions and role templates into the DB.

    - Ensures all permissions exist in collection `permissions`.
    - Ensures role documents exist/are updated in collection `roles` with sorted unique permissions.
    """
    # Permissions
    for name, description in DEFAULT_PERMISSIONS.items():
        db["permissions"].update_one(
            {"name": name},
            {"$setOnInsert": {"name": name, "description": description}},
            upsert=True,
        )

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
