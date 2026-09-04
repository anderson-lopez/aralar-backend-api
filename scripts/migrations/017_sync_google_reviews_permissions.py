"""
Migración 017: Sincronizar permisos de google_reviews con el catálogo actualizado

Esta migración:
1. Ejecuta apply_catalog() para crear los nuevos permisos y actualizar roles.
2. Aplica descripciones específicas para los permisos de google_reviews.

Es idempotente - se puede ejecutar múltiples veces.

Permisos agregados:
- google_reviews:read
- google_reviews:create
- google_reviews:update
- google_reviews:delete
- google_reviews:moderate
- google_reviews:sync
"""

import sys
import os

# Add project root to path to import role_catalog
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aralar.catalog.role_catalog import apply_catalog

GOOGLE_REVIEWS_DESCRIPTIONS = {
    "google_reviews:read": "Ver reseñas de Google y la bandeja de moderación",
    "google_reviews:create": "Dar de alta reseñas manualmente",
    "google_reviews:update": "Editar destacado y orden de reseñas",
    "google_reviews:delete": "Eliminar reseñas",
    "google_reviews:moderate": "Aprobar o rechazar reseñas",
    "google_reviews:sync": "Sincronizar reseñas desde el origen",
}


def up(db):
    print("[017] Sincronizando permisos y roles de google_reviews...")

    # 1. Aplicar catálogo (crea permisos y actualiza roles)
    apply_catalog(db)

    # 2. Aplicar descripciones específicas
    print("[017] Aplicando descripciones de permisos de google_reviews...")
    updated_count = 0
    for permission_name, description in GOOGLE_REVIEWS_DESCRIPTIONS.items():
        result = db["permissions"].update_one(
            {"name": permission_name},
            {"$set": {"description": description}},
            upsert=True,
        )
        if result.matched_count > 0 or result.upserted_id:
            updated_count += 1

    print(f"[017] Migración completada - {updated_count} permisos con descripciones aplicadas")


def down(db):
    print("[017 rollback] Revirtiendo descripciones de permisos de google_reviews...")
    result = db["permissions"].update_many(
        {"name": {"$in": list(GOOGLE_REVIEWS_DESCRIPTIONS.keys())}},
        {"$set": {"description": ""}},
    )
    print(f"[017 rollback] Revertidas {result.modified_count} descripciones")
