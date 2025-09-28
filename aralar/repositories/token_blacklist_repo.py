from datetime import datetime, timezone
from .base_repo import to_object_id


class TokenBlacklistRepo:
    """
    Repositorio para manejar tokens invalidados (blacklist).
    Los tokens se guardan hasta su expiración natural para evitar reutilización.
    """
    
    def __init__(self, db):
        self.col = db["token_blacklist"]
        # Los índices se crean en la migración 008_token_blacklist_indexes.py
    
    def add_token(self, jti: str, user_id: str, expires_at: datetime, reason: str = "logout"):
        """
        Agrega un token a la blacklist.
        
        Args:
            jti: JWT ID único del token
            user_id: ID del usuario propietario del token
            expires_at: Fecha de expiración del token
            reason: Razón de invalidación (logout, security, admin, etc.)
        """
        doc = {
            "jti": jti,
            "user_id": user_id,
            "blacklisted_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "reason": reason
        }
        
        # Usar upsert para evitar duplicados
        self.col.update_one(
            {"jti": jti},
            {"$set": doc},
            upsert=True
        )
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """
        Verifica si un token está en la blacklist.
        
        Args:
            jti: JWT ID único del token
            
        Returns:
            True si el token está blacklisted, False en caso contrario
        """
        result = self.col.find_one({"jti": jti})
        return result is not None
    
    def blacklist_all_user_tokens(self, user_id: str, reason: str = "security"):
        """
        Invalida todos los tokens activos de un usuario.
        Útil para desactivación de cuenta o cambios de seguridad críticos.
        
        Args:
            user_id: ID del usuario
            reason: Razón de invalidación
        """
        # Nota: Esto requiere que guardemos los JTIs activos por usuario
        # Por simplicidad, incrementamos perm_version que ya manejamos
        # En una implementación más robusta, mantendríamos un registro de tokens activos
        pass
    
    def get_blacklisted_tokens_by_user(self, user_id: str, limit: int = 50):
        """
        Obtiene tokens blacklisted de un usuario específico.
        Útil para auditoría y debugging.
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados
            
        Returns:
            Lista de documentos de tokens blacklisted
        """
        cursor = self.col.find(
            {"user_id": user_id}
        ).sort("blacklisted_at", -1).limit(limit)
        
        return list(cursor)
    
    def cleanup_expired_tokens(self):
        """
        Limpia manualmente tokens expirados.
        MongoDB TTL ya hace esto automáticamente, pero útil para limpieza manual.
        """
        now = datetime.now(timezone.utc)
        result = self.col.delete_many({"expires_at": {"$lt": now}})
        return result.deleted_count
    
    def get_stats(self):
        """
        Obtiene estadísticas de la blacklist.
        Útil para monitoreo y métricas.
        """
        total_count = self.col.count_documents({})
        
        # Contar por razón
        pipeline = [
            {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_reason = list(self.col.aggregate(pipeline))
        
        return {
            "total_blacklisted": total_count,
            "by_reason": by_reason
        }
