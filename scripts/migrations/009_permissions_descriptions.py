# Migración para agregar descripciones amigables a los permisos
# Fecha: 2025-09-28

PERMISSIONS_DESCRIPTIONS = {
    # Permisos de usuarios
    "users:read": "Ver información de usuarios y perfiles",
    "users:create": "Crear nuevos usuarios en el sistema",
    "users:assign_roles": "Asignar y modificar roles de usuarios",
    "users:assign_permissions": "Asignar permisos específicos a usuarios",
    "users:activate": "Activar y desactivar cuentas de usuario",
    
    # Permisos de roles (granulares)
    "roles:read": "Ver roles del sistema",
    "roles:create": "Crear nuevos roles",
    "roles:update": "Modificar roles existentes", 
    "roles:delete": "Eliminar roles del sistema",
    "roles:permissions:read": "Ver catálogo de permisos disponibles",
    "roles:permissions:update": "Modificar descripciones de permisos",
    
    # Permisos de menús (incluye i18n y uploads)
    "menus:read": "Ver menús y sus contenidos",
    "menus:create": "Crear nuevos menús",
    "menus:update": "Modificar menús, traducciones y subir archivos",
    "menus:delete": "Eliminar menús del sistema",
    "menus:publish": "Publicar y despublicar menús",
    
    # Permisos de plantillas de menús
    "menu_templates:read": "Ver plantillas de menús disponibles",
    "menu_templates:create": "Crear nuevas plantillas de menús",
    "menu_templates:update": "Modificar plantillas de menús existentes",
    "menu_templates:publish": "Publicar y despublicar plantillas",
    "menu_templates:archive": "Archivar y desarchivar plantillas",
    
    # Permisos de autenticación (admin)
    "auth:invalidate_tokens": "Invalidar tokens de otros usuarios (admin)",
    "auth:view_blacklist": "Ver historial de tokens invalidados (admin)",
    
    # Permisos de reservas (futuro)
    "reservas:read": "Ver reservas y su información",
    "reservas:create": "Crear nuevas reservas",
    "reservas:update": "Modificar reservas existentes",
    "reservas:delete": "Cancelar y eliminar reservas",
}


def up(db):
    """Actualizar descripciones de permisos existentes"""
    print("Updating permissions descriptions...")
    
    updated_count = 0
    for permission_name, description in PERMISSIONS_DESCRIPTIONS.items():
        result = db["permissions"].update_one(
            {"name": permission_name},
            {"$set": {"description": description}},
            upsert=True
        )
        
        if result.matched_count > 0:
            print(f"✓ Updated description for: {permission_name}")
            updated_count += 1
        elif result.upserted_id:
            print(f"✓ Created new permission: {permission_name}")
            updated_count += 1
    
    print(f"Permissions descriptions updated successfully! ({updated_count} permissions)")


def down(db):
    """Revertir descripciones a vacío"""
    print("Reverting permissions descriptions...")
    
    result = db["permissions"].update_many(
        {"name": {"$in": list(PERMISSIONS_DESCRIPTIONS.keys())}},
        {"$set": {"description": ""}}
    )
    
    print(f"Reverted {result.modified_count} permission descriptions")
