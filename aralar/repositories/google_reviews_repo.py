from datetime import datetime

from .base_repo import to_object_id


class GoogleReviewsRepo:
    """Acceso a la colección `google_reviews`.

    La clave de identidad es la terna **`(tenant_id, provider, external_id)`**, con
    índice único. `external_id` es el id estable que da el origen (Google o el alta
    manual), no el nombre del autor ni la fecha: las fechas relativas del scraping
    ("hace 3 semanas") cambian solas y usarlas como clave duplicaría cada reseña en
    cada sincronización.
    """

    def __init__(self, db):
        self.col = db["google_reviews"]

    def insert(self, doc: dict):
        doc["created_at"] = doc.get("created_at") or datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        res = self.col.insert_one(doc)
        return str(res.inserted_id)

    def get(self, _id: str):
        return self.col.find_one({"_id": to_object_id(_id)})

    def get_by_external_id(self, tenant_id: str, provider: str, external_id: str):
        return self.col.find_one(
            {"tenant_id": tenant_id, "provider": provider, "external_id": external_id}
        )

    def list(self, filters: dict | None = None, skip: int = 0, limit: int = 20):
        filters = filters or {}
        cur = self.col.find(filters).sort([("published_at", -1)]).skip(skip)
        if limit:
            cur = cur.limit(limit)
        return list(cur)

    def count(self, filters: dict | None = None) -> int:
        return self.col.count_documents(filters or {})

    def find_public(self, tenant_id: str | None = None):
        """Reseñas aprobadas. El orden final se aplica en el service (nulls al final)."""
        q: dict = {"status": "approved"}
        if tenant_id:
            q["tenant_id"] = tenant_id
        return list(self.col.find(q))

    def update(self, _id: str, patch: dict):
        patch["updated_at"] = datetime.utcnow()
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": patch})
        return self.get(_id)

    def delete(self, _id: str) -> int:
        res = self.col.delete_one({"_id": to_object_id(_id)})
        return res.deleted_count
