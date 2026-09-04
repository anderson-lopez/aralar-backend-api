"""
Migración 014: Colección `menu_services` (clasificación "Otros servicios")

Esta migración:
1. Crea la colección `menu_services` con sus índices (slug único por tenant).
2. Siembra los 3 servicios iniciales si la colección está vacía
   (Desayunos, Lunch, Comida para llevar).
3. Normaliza los menús existentes: `service_slugs: []` donde falte, para que
   el filtro de `/public/available` (que excluye menús con servicios) trabaje
   sobre un campo siempre presente.

Es idempotente: se puede ejecutar varias veces sin duplicar datos.
"""

from datetime import datetime


DEFAULT_TENANT = "aralar"

DEFAULT_SERVICES = [
    {
        "slug": "desayunos",
        "name": "Desayunos",
        "labels": {"es-ES": "Desayunos", "en-GB": "Breakfast"},
        "order": 1,
    },
    {
        "slug": "lunch",
        "name": "Lunch",
        "labels": {"es-ES": "Lunch", "en-GB": "Lunch"},
        "order": 2,
    },
    {
        "slug": "comida-para-llevar",
        "name": "Comida para llevar",
        "labels": {"es-ES": "Comida para llevar", "en-GB": "Takeaway"},
        "order": 3,
    },
]


def up(db):
    coll = db["menu_services"]

    # Índices
    coll.create_index([("tenant_id", 1), ("slug", 1)], unique=True)
    coll.create_index("is_active")
    coll.create_index("order")

    # Seed inicial (solo si está vacía)
    if coll.count_documents({}) == 0:
        now = datetime.utcnow()
        docs = [
            {
                "tenant_id": DEFAULT_TENANT,
                "slug": s["slug"],
                "name": s["name"],
                "labels": s["labels"],
                "order": s["order"],
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
            for s in DEFAULT_SERVICES
        ]
        coll.insert_many(docs)
        print(f"[014] OK: {len(docs)} servicios iniciales creados")
    else:
        print("[014] OK: coleccion menu_services ya tiene documentos")

    # Normalizar menús existentes: service_slugs siempre presente
    res = db["menus"].update_many(
        {"service_slugs": {"$exists": False}},
        {"$set": {"service_slugs": []}},
    )
    print(f"[014] OK: {res.modified_count} menus normalizados con service_slugs=[]")


def down(db):
    db.drop_collection("menu_services")
    db["menus"].update_many({}, {"$unset": {"service_slugs": ""}})
    print("[014 rollback] Coleccion menu_services eliminada y service_slugs removido de menus")
