from .base_repo import to_object_id
from datetime import datetime
from pymongo.errors import DuplicateKeyError


class MenuTemplatesRepo:
    def __init__(self, db):
        self.col = db["menu_templates"]

    def insert(self, doc: dict):
        doc["created_at"] = doc.get("created_at") or datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        
        try:
            res = self.col.insert_one(doc)
            return str(res.inserted_id)
        except DuplicateKeyError as e:
            # Extraer información del error para mensaje más claro
            slug = doc.get("slug", "unknown")
            version = doc.get("version", "unknown")
            raise ValueError(f"Template with slug '{slug}' and version '{version}' already exists") from e

    def get(self, _id: str):
        return self.col.find_one({"_id": to_object_id(_id)})

    def get_by_slug_version(self, slug: str, version: int):
        return self.col.find_one({"slug": slug, "version": version})

    def list(self, filters: dict, skip=0, limit=20):
        return list(self.col.find(filters).skip(skip).limit(limit).sort("updated_at", -1))

    def update(self, _id: str, patch: dict):
        patch["updated_at"] = datetime.utcnow()
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": patch})
        return self.get(_id)
