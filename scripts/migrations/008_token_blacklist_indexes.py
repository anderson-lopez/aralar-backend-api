"""
Migración 008: Índices para token blacklist
Crea los índices necesarios para la colección token_blacklist
"""

def up(db):
    """Crear índices para token blacklist"""
    
    # Colección de tokens blacklisted
    blacklist_col = db["token_blacklist"]
    
    print("Creating token_blacklist indexes...")
    
    # Índice TTL para auto-eliminación de tokens expirados
    # MongoDB eliminará automáticamente documentos cuando expires_at < now
    blacklist_col.create_index(
        "expires_at", 
        expireAfterSeconds=0,
        name="ttl_expires_at"
    )
    print("✓ Created TTL index on expires_at")
    
    # Índice único para JTI (JWT ID) - búsquedas rápidas
    blacklist_col.create_index(
        "jti", 
        unique=True,
        name="unique_jti"
    )
    print("✓ Created unique index on jti")
    
    # Índice para consultas por usuario (historial, auditoría)
    blacklist_col.create_index(
        "user_id",
        name="idx_user_id"
    )
    print("✓ Created index on user_id")
    
    # Índice compuesto para consultas de historial por usuario ordenadas por fecha
    blacklist_col.create_index(
        [("user_id", 1), ("blacklisted_at", -1)],
        name="idx_user_history"
    )
    print("✓ Created compound index on user_id + blacklisted_at")
    
    # Índice para consultas por razón (estadísticas, auditoría)
    blacklist_col.create_index(
        "reason",
        name="idx_reason"
    )
    print("✓ Created index on reason")
    
    print("Token blacklist indexes created successfully!")


def down(db):
    """Eliminar índices de token blacklist"""
    
    blacklist_col = db["token_blacklist"]
    
    print("Dropping token_blacklist indexes...")
    
    # Eliminar índices específicos por nombre
    try:
        blacklist_col.drop_index("ttl_expires_at")
        print("✓ Dropped TTL index on expires_at")
    except Exception as e:
        print(f"⚠ Could not drop ttl_expires_at: {e}")
    
    try:
        blacklist_col.drop_index("unique_jti")
        print("✓ Dropped unique index on jti")
    except Exception as e:
        print(f"⚠ Could not drop unique_jti: {e}")
    
    try:
        blacklist_col.drop_index("idx_user_id")
        print("✓ Dropped index on user_id")
    except Exception as e:
        print(f"⚠ Could not drop idx_user_id: {e}")
    
    try:
        blacklist_col.drop_index("idx_user_history")
        print("✓ Dropped compound index on user_id + blacklisted_at")
    except Exception as e:
        print(f"⚠ Could not drop idx_user_history: {e}")
    
    try:
        blacklist_col.drop_index("idx_reason")
        print("✓ Dropped index on reason")
    except Exception as e:
        print(f"⚠ Could not drop idx_reason: {e}")
    
    print("Token blacklist indexes rollback completed!")


if __name__ == "__main__":
    # Para testing local
    from pymongo import MongoClient
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["aralar"]
    
    print("Running migration 008...")
    up(db)
    print("Migration 008 completed!")
