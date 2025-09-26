import importlib.util
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
# Ensure project root (one level up) is on sys.path when running from scripts/
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from aralar.config import BaseConfig as Config

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def load_module_from_path(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def main():
    # Ensure .env is loaded so Config picks up environment values
    load_dotenv()
    mongo_uri = Config.MONGO_URI
    client = MongoClient(mongo_uri)
    db = client.get_default_database()
    applied = {m["name"] for m in db["schema_migrations"].find({}, {"name": 1})}

    files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".py"))
    for fname in files:
        name = fname[:-3]  # sin .py
        if name in applied:
            continue
        path = os.path.join(MIGRATIONS_DIR, fname)
        mod = load_module_from_path(path)
        if not hasattr(mod, "up"):
            raise RuntimeError(f"Migration {name} missing up()")
        print(f"[migrate] applying {name} ...")
        mod.up(db)  # ejecutar migración
        db["schema_migrations"].insert_one(
            {
                "name": name,
                "applied_at": datetime.utcnow(),
            }
        )
        print(f"[migrate] done {name}")


if __name__ == "__main__":
    main()
