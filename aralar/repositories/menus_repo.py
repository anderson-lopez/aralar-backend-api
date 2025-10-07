from .base_repo import to_object_id
from datetime import datetime


class MenusRepo:
    def __init__(self, db):
        self.col = db["menus"]

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

    def list_featured_by_day(self, *, locale: str, date_iso: str, weekday: str):
        """Devuelve menús destacados publicados para un locale en un día concreto.

        date_iso: 'YYYY-MM-DD' (string)
        weekday: uno de 'MON'..'SUN'
        """
        locale_status_field = f"publish.{locale}.status"
        q = {
            "status": "published",
            locale_status_field: "published",
            "featured": True,  # Solo menus destacados
            "availability.days_of_week": weekday,
            "availability.date_ranges": {
                "$elemMatch": {
                    "start": {"$lte": date_iso},
                    "end": {"$gte": date_iso},
                }
            },
        }
        # Ordenar por featured_order (nulls last) y luego por updated_at
        return list(self.col.find(q).sort([
            ("featured_order", 1),  # Ascending order (lower numbers first)
            ("updated_at", -1)      # Most recent first for same order
        ]))
