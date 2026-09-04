"""
Migración 016: Colección `google_reviews` (reseñas para la landing)

Esta migración:
1. Crea la colección `google_reviews` con sus índices.
2. El índice único `(tenant_id, provider, external_id)` es la clave del upsert
   idempotente del sync: garantiza que re-sincronizar no duplique reseñas.

Es idempotente: se puede ejecutar varias veces sin duplicar datos.
"""


def up(db):
    coll = db["google_reviews"]

    # Clave de identidad del upsert. `external_id` es el id estable del origen;
    # usar autor+fecha no sirve porque la fecha relativa de Google cambia sola.
    coll.create_index(
        [("tenant_id", 1), ("provider", 1), ("external_id", 1)],
        unique=True,
        name="uniq_tenant_provider_external",
    )
    # Bandeja de moderación del panel y filtro del listado público.
    coll.create_index([("tenant_id", 1), ("status", 1), ("rating", -1)], name="tenant_status_rating")
    coll.create_index("display_order", name="display_order_idx")
    coll.create_index([("published_at", -1)], name="published_at_idx")

    print("[016] OK: coleccion google_reviews e indices creados")


def down(db):
    db.drop_collection("google_reviews")
    print("[016 rollback] Coleccion google_reviews eliminada")
