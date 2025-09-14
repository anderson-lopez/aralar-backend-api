from datetime import datetime
from dotenv import load_dotenv
import os
import sys
from argon2 import PasswordHasher
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()
# Ensure project root (one level up) is on sys.path when running from scripts/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from aralar.config import BaseConfig as Config

DEFAULT_PERMISSIONS = [
    # usuarios
    "users:read",
    "users:create",
    "users:update",
    "users:delete",
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
    # (futuro) menus / reservas
    "menus:read",
    "menus:create",
    "menus:update",
    "menus:delete",
    "reservas:read",
    "reservas:create",
    "reservas:update",
    "reservas:delete",
    "menus:publish",
    "menus:validate",
    "menu_templates:read",
    "menu_templates:create",
    "menu_templates:update",
    "menu_templates:delete",
    "menu_templates:publish",
    "menu_templates:validate",
    "menu_templates:archive",
]

ROLE_TEMPLATES = {
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
}


def main():
    mongo_uri = Config.MONGO_URI
    client = MongoClient(mongo_uri)
    db = client.get_default_database()

    # Índices mínimos
    db["users"].create_index("email", unique=True)
    db["roles"].create_index("name", unique=True)
    db["permissions"].create_index("name", unique=True)

    # Carga catálogo de permisos
    for p in DEFAULT_PERMISSIONS:
        db["permissions"].update_one({"name": p}, {"$set": {"description": ""}}, upsert=True)

    # Crea/actualiza roles base
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

    # Usuario admin
    email = Config.SEED_ADMIN_EMAIL
    full_name = Config.SEED_ADMIN_FULLNAME
    password = Config.SEED_ADMIN_PASSWORD

    existing = db["users"].find_one({"email": email})
    if not existing:
        ph = PasswordHasher()
        user_doc = {
            "email": email,
            "full_name": full_name,
            "password_hash": ph.hash(password),
            "roles": ["admin"],
            "is_active": True,
            "created_at": datetime.utcnow(),
        }
        res = db["users"].insert_one(user_doc)
        print(f"[seed] Usuario admin creado: {email} (id={res.inserted_id})")
    else:
        # asegúrate de que tenga el rol admin
        roles = set(existing.get("roles", [])) | {"admin"}
        db["users"].update_one({"_id": existing["_id"]}, {"$set": {"roles": list(roles)}})
        print(f"[seed] Usuario admin ya existía, roles actualizados: {email}")

    print("[seed] OK")


if __name__ == "__main__":
    main()
