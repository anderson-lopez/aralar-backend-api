from datetime import datetime
from hashlib import sha1


class TranslationsRepo:
    def __init__(self, db):
        self.col = db["translations_cache"]

    @staticmethod
    def make_hash(text: str, src: str, tgt: str, provider: str, glossary_version: int | None):
        key = f"{text}\u241f{src}\u241f{tgt}\u241f{provider}\u241f{glossary_version or 0}"
        return sha1(key.encode("utf-8")).hexdigest()

    def get(self, h: str):
        return self.col.find_one({"hash": h})

    def get_by_tenant(self, tenant_id: str, limit: int = 100):
        """Obtiene traducciones recientes de un tenant específico"""
        return list(self.col.find(
            {"tenant_id": tenant_id}
        ).sort("created_at", -1).limit(limit))

    def count_by_tenant(self, tenant_id: str):
        """Cuenta las traducciones en cache de un tenant"""
        return self.col.count_documents({"tenant_id": tenant_id})

    def clear_tenant_cache(self, tenant_id: str):
        """Limpia el cache de traducciones de un tenant específico"""
        return self.col.delete_many({"tenant_id": tenant_id})

    def put(self, h: str, doc: dict):
        doc["hash"] = h
        doc["created_at"] = datetime.utcnow()
        try:
            self.col.insert_one(doc)
        except Exception:
            pass
