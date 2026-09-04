from .base_repo import to_object_id
from datetime import datetime


class MenuServicesRepo:
    """Acceso a la colección `menu_services` (catálogo de servicios de menú).

    Un "servicio" es una etiqueta gestionable (Desayunos, Lunch, Comida para
    llevar, …) que clasifica menús para la sección pública "Otros servicios".
    El `slug` es estable y único por tenant; es lo que referencian los menús en
    su campo `service_slugs`.
    """

    def __init__(self, db):
        self.col = db["menu_services"]

    def insert(self, doc: dict):
        doc["created_at"] = doc.get("created_at") or datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        res = self.col.insert_one(doc)
        return str(res.inserted_id)

    def get(self, _id: str):
        return self.col.find_one({"_id": to_object_id(_id)})

    def get_by_slug(self, tenant_id: str, slug: str):
        return self.col.find_one({"tenant_id": tenant_id, "slug": slug})

    def list(self, filters: dict | None = None):
        filters = filters or {}
        return list(self.col.find(filters).sort([("order", 1), ("name", 1)]))

    def find_active(self, tenant_id: str | None = None):
        q: dict = {"is_active": True}
        if tenant_id:
            q["tenant_id"] = tenant_id
        return list(self.col.find(q).sort([("order", 1), ("name", 1)]))

    def update(self, _id: str, patch: dict):
        patch["updated_at"] = datetime.utcnow()
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": patch})
        return self.get(_id)

    def delete(self, _id: str) -> int:
        res = self.col.delete_one({"_id": to_object_id(_id)})
        return res.deleted_count
