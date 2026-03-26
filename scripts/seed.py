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
from aralar.catalog.role_catalog import DEFAULT_PERMISSIONS, ROLE_TEMPLATES


def main():
    mongo_uri = Config.MONGO_URI
    client = MongoClient(mongo_uri)
    db = client.get_default_database()

    # Índices mínimos
    db["users"].create_index("email", unique=True)
    db["roles"].create_index("name", unique=True)
    db["permissions"].create_index("name", unique=True)

    # Catálogo de permisos y roles (idempotente) desde un único origen
    # Solo crear permisos que no existen, preservando descripciones existentes
    for name, description in DEFAULT_PERMISSIONS.items():
        db["permissions"].update_one(
            {"name": name},
            {"$setOnInsert": {"name": name, "description": description}},
            upsert=True,
        )

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
