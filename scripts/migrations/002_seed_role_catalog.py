DEFAULT_PERMISSIONS = [
    "users:read",
    "users:create",
    "users:update",
    "users:delete",
    "users:assign_roles",
    "menus:read",
    "menus:create",
    "menus:update",
    "menus:delete",
    "reservas:read",
    "reservas:create",
    "reservas:update",
    "reservas:delete",
]

ROLE_TEMPLATES = {
    "admin": {
        "description": "Administrador del sistema con todos los permisos",
        "permissions": DEFAULT_PERMISSIONS,
    },
    "manager": {
        "description": "Gestión operativa",
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
        "description": "Acceso mínimo",
        "permissions": ["menus:read", "reservas:read", "reservas:create"],
    },
}


def up(db):
    for p in DEFAULT_PERMISSIONS:
        db["permissions"].update_one({"name": p}, {"$set": {"description": ""}}, upsert=True)
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
