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

    def count(self, filters: dict) -> int:
        return self.col.count_documents(filters)

    def update(self, _id: str, patch: dict):
        patch["updated_at"] = datetime.utcnow()
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": patch})
        return self.get(_id)

    def delete(self, _id: str) -> int:
        """Elimina definitivamente un menú de la colección.
        Devuelve el número de documentos eliminados (0 o 1)."""
        res = self.col.delete_one({"_id": to_object_id(_id)})
        return res.deleted_count

    def set_availability(self, _id: str, availability: dict):
        """Guarda el bloque de disponibilidad normalizado en el documento."""
        update = {
            "availability": availability,
            "updated_at": datetime.utcnow(),
        }
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": update})
        return self.get(_id)

    def list_published_by_day(self, *, date_iso: str, weekday: str):
        """Devuelve menús públicos disponibles en un día concreto, SIN filtrar por idioma.

        No gateamos por `publish.{locale}.status` a propósito: un menú con
        `status == "published"` ya tiene garantizado ≥1 locale publicado (lo exige
        `validate_menu` en la publicación global), así que el listado debe salir
        aunque el idioma pedido no exista para ese menú. El idioma efectivo a
        mostrar se resuelve en el service (`effective_locale`).

        date_iso: 'YYYY-MM-DD' (string)
        weekday: uno de 'MON'..'SUN'
        """
        q = {
            "status": "published",
            "availability.days_of_week": weekday,
            "availability.date_ranges": {
                "$elemMatch": {
                    "start": {"$lte": date_iso},
                    "end": {"$gte": date_iso},
                }
            },
            # Los menús clasificados en algún servicio salen SOLO en la sección
            # "Otros servicios" (list_service_menus_by_day), no aquí.
            "$or": [
                {"service_slugs": {"$exists": False}},
                {"service_slugs": {"$size": 0}},
            ],
        }
        return list(self.col.find(q).sort("updated_at", -1))

    def list_service_menus_by_day(self, *, service_slug: str, date_iso: str, weekday: str):
        """Devuelve menús publicados de un servicio concreto disponibles en un día.

        Mismo gate de status + availability que `list_published_by_day`, pero
        en vez de excluir los clasificados, filtra por pertenencia al servicio:
        `service_slugs: service_slug` (equality sobre array = "contiene el slug").
        No gatea por idioma (igual que el listado público general).

        date_iso: 'YYYY-MM-DD' (string)
        weekday: uno de 'MON'..'SUN'
        """
        q = {
            "status": "published",
            "service_slugs": service_slug,
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
        return list(
            self.col.find(q).sort(
                [
                    ("featured_order", 1),  # Ascending order (lower numbers first)
                    ("updated_at", -1),  # Most recent first for same order
                ]
            )
        )

    def count_by_template(self, template_slug: str, template_version: int) -> int:
        """Count menus using a specific template by slug and version"""
        return self.col.count_documents({
            "template_slug": template_slug,
            "template_version": template_version
        })
