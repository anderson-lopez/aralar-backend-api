from .base_repo import to_object_id
from datetime import datetime


class MenusRepo:
    def __init__(self, db):
        self.col = db["menus"]
        self.col.create_index([("tenant_id", 1)])
        self.col.create_index([("template_slug", 1), ("template_version", 1)])
        self.col.create_index([("status", 1)])
        # índices de availability ya los cubrimos antes

    def insert(self, doc: dict):
        doc["created_at"] = doc.get("created_at") or datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        res = self.col.insert_one(doc)
        return str(res.inserted_id)

    def get(self, _id: str):
        return self.col.find_one({"_id": to_object_id(_id)})

    def list(self, filters: dict, skip=0, limit=20):
        return list(self.col.find(filters).skip(skip).limit(limit).sort("updated_at", -1))

    def update(self, _id: str, patch: dict):
        patch["updated_at"] = datetime.utcnow()
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": patch})
        return self.get(_id)

    def set_availability(self, _id: str, availability: dict):
        """Guarda el bloque de disponibilidad normalizado en el documento."""
        update = {
            "availability": availability,
            "updated_at": datetime.utcnow(),
        }
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": update})
        return self.get(_id)

    def list_published_by_day(self, *, locale: str, date_iso: str, weekday: str):
        """Devuelve menús publicados para un locale en un día concreto.

        date_iso: 'YYYY-MM-DD' (string)
        weekday: uno de 'MON'..'SUN'
        """
        locale_status_field = f"publish.{locale}.status"
        q = {
            "status": "published",
            locale_status_field: "published",
            "availability.days_of_week": weekday,
            "availability.date_ranges": {
                "$elemMatch": {
                    "start": {"$lte": date_iso},
                    "end": {"$gte": date_iso},
                }
            },
        }
        return list(self.col.find(q).sort("updated_at", -1))
