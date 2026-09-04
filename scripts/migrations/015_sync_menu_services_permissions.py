"""
Migración 015: Sincronizar permisos de menu_services con el catálogo actualizado

Esta migración:
1. Ejecuta apply_catalog() para crear los nuevos permisos y actualizar roles.
2. Aplica descripciones específicas para los permisos de menu_services.

Es idempotente - se puede ejecutar múltiples veces.

Permisos agregados:
- menu_services:read
- menu_services:create
- menu_services:update
- menu_services:delete
"""

import sys
import os

# Add project root to path to import role_catalog
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aralar.catalog.role_catalog import apply_catalog

MENU_SERVICES_DESCRIPTIONS = {
    "menu_services:read": "Ver servicios de menú (Otros servicios)",
    "menu_services:create": "Crear servicios de menú",
    "menu_services:update": "Editar servicios de menú",
    "menu_services:delete": "Eliminar servicios de menú",
}


def up(db):
    print("[015] Sincronizando permisos y roles de menu_services...")

    # 1. Aplicar catálogo (crea permisos y actualiza roles)
    apply_catalog(db)

    # 2. Aplicar descripciones específicas
    print("[015] Aplicando descripciones de permisos de menu_services...")
    updated_count = 0
    for permission_name, description in MENU_SERVICES_DESCRIPTIONS.items():
        result = db["permissions"].update_one(
            {"name": permission_name},
            {"$set": {"description": description}},
            upsert=True,
        )
        if result.matched_count > 0 or result.upserted_id:
            updated_count += 1

    print(f"[015] Migración completada - {updated_count} permisos con descripciones aplicadas")


def down(db):
    print("[015 rollback] Revirtiendo descripciones de permisos de menu_services...")
    result = db["permissions"].update_many(
        {"name": {"$in": list(MENU_SERVICES_DESCRIPTIONS.keys())}},
        {"$set": {"description": ""}},
    )
    print(f"[015 rollback] Revertidas {result.modified_count} descripciones")
