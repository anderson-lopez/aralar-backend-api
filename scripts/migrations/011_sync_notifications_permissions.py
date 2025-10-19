"""
Migración 011: Sincronizar permisos de notifications con el catálogo actualizado

Esta migración:
1. Agrega los nuevos permisos de notifications con descripciones
2. Actualiza los roles existentes con los permisos apropiados
3. Es idempotente - se puede ejecutar múltiples veces

Los permisos agregados:
- notifications:read
- notifications:create
- notifications:update
- notifications:delete
"""

import sys
import os

# Add project root to path to import role_catalog
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aralar.catalog.role_catalog import apply_catalog

# Descripciones específicas para permisos de notifications
NOTIFICATIONS_DESCRIPTIONS = {
    "notifications:read": "Ver notificaciones del sistema y sus detalles",
    "notifications:create": "Crear nuevas notificaciones para usuarios",
    "notifications:update": "Modificar notificaciones existentes y cambiar estado",
    "notifications:delete": "Eliminar notificaciones del sistema",
}


def up(db):
    """
    1. Ejecuta apply_catalog() que sincroniza automáticamente permisos y roles
    2. Aplica descripciones específicas para permisos de notifications
    
    Es idempotente - se puede ejecutar múltiples veces sin problemas.
    """
    print("[011] Sincronizando permisos y roles de notifications...")
    
    # 1. Aplicar catálogo (crea permisos y actualiza roles)
    apply_catalog(db)
    
    # 2. Aplicar descripciones específicas para notifications (siguiendo patrón migración 009)
    print("[011] Aplicando descripciones de permisos de notifications...")
    updated_count = 0
    
    for permission_name, description in NOTIFICATIONS_DESCRIPTIONS.items():
        result = db["permissions"].update_one(
            {"name": permission_name},
            {"$set": {"description": description}},
            upsert=True  # Por si acaso el permiso no existiera aún
        )
        
        if result.matched_count > 0:
            print(f"[011] ✓ Descripción actualizada para: {permission_name}")
            updated_count += 1
        elif result.upserted_id:
            print(f"[011] ✓ Creado permiso con descripción: {permission_name}")
            updated_count += 1
    
    # 3. Verificaciones
    new_permissions = list(NOTIFICATIONS_DESCRIPTIONS.keys())
    
    for perm in new_permissions:
        existing = db["permissions"].find_one({"name": perm})
        if existing:
            desc = existing.get("description", "")
            print(f"[011] ✓ Permiso '{perm}' - Descripción: '{desc}'")
        else:
            print(f"[011] ✗ Error: Permiso '{perm}' no encontrado")
    
    # Verificar que roles fueron actualizados
    roles_to_check = ["admin", "manager", "staff", "user"]
    for role_name in roles_to_check:
        role = db["roles"].find_one({"name": role_name})
        if role:
            notifications_perms = [p for p in role.get("permissions", []) if p.startswith("notifications:")]
            print(f"[011] ✓ Rol '{role_name}' tiene {len(notifications_perms)} permisos de notifications")
        else:
            print(f"[011] ✗ Rol '{role_name}' no encontrado")
    
    print(f"[011] Migración completada - {updated_count} permisos con descripciones aplicadas")


def down(db):
    """
    Rollback: Revertir descripciones de permisos de notifications (no eliminar permisos)
    Siguiendo el patrón conservador de la migración 009
    """
    print("[011 rollback] Revirtiendo descripciones de permisos de notifications...")
    
    result = db["permissions"].update_many(
        {"name": {"$in": list(NOTIFICATIONS_DESCRIPTIONS.keys())}},
        {"$set": {"description": ""}}
    )
    
    print(f"[011 rollback] Revertidas {result.modified_count} descripciones de permisos de notifications")
    print("[011 rollback] Rollback completado")
