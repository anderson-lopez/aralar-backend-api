import importlib.util
import os
from datetime import datetime
from pymongo import MongoClient

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def load_module_from_path(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def main():
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/aralar")
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
