from datetime import datetime, timezone
from flask_jwt_extended import decode_token
from flask import current_app


class TokenBlacklistService:
    """
    Servicio para manejar la lógica de negocio de token blacklist.
    Proporciona métodos de alto nivel para invalidar tokens.
    """
    
    def __init__(self, repo):
        self.repo = repo
    
    def logout_token(self, token: str, user_id: str):
        """
        Invalida un token específico por logout.
        
        Args:
            token: Token JWT completo
            user_id: ID del usuario (para validación)
            
        Returns:
            True si se invalidó correctamente
        """
        try:
            # Decodificar token para obtener JTI y expiración
            decoded = decode_token(token)
            jti = decoded.get("jti")
            exp = decoded.get("exp")
            token_user_id = decoded.get("sub")
            
            # Validar que el token pertenece al usuario
            if token_user_id != user_id:
                raise ValueError("Token does not belong to user")
            
            if not jti:
                raise ValueError("Token missing JTI")
            
            # Convertir timestamp de expiración a datetime
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            
            # Agregar a blacklist
            blacklisted_at = datetime.now(timezone.utc)
            self.repo.add_token(
                jti=jti,
                user_id=user_id,
                expires_at=expires_at,
                reason="logout"
            )
            
            return {
                "blacklisted_at": blacklisted_at,
                "jti": jti
            }
            
        except Exception as e:
            current_app.logger.error(f"Error blacklisting token: {str(e)}")
            raise ValueError(f"Failed to blacklist token: {str(e)}")
    
    def invalidate_token_by_admin(self, token: str, admin_user_id: str, reason: str = "admin_action"):
        """
        Invalida un token por acción administrativa.
        
        Args:
            token: Token JWT completo
            admin_user_id: ID del administrador que ejecuta la acción
            reason: Razón específica de invalidación
            
        Returns:
            True si se invalidó correctamente
        """
        try:
            decoded = decode_token(token)
            jti = decoded.get("jti")
            exp = decoded.get("exp")
            token_user_id = decoded.get("sub")
            
            if not jti:
                raise ValueError("Token missing JTI")
            
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
            
            # Agregar a blacklist con razón administrativa
            self.repo.add_token(
                jti=jti,
                user_id=token_user_id,
                expires_at=expires_at,
                reason=f"{reason}_by_{admin_user_id}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error invalidating token by admin: {str(e)}")
            raise ValueError(f"Failed to invalidate token: {str(e)}")
    
    def is_token_valid(self, jti: str) -> bool:
        """
        Verifica si un token es válido (no está en blacklist).
        
        Args:
            jti: JWT ID único del token
            
        Returns:
            True si el token es válido, False si está blacklisted
        """
        return not self.repo.is_token_blacklisted(jti)
    
    def invalidate_user_tokens_for_security(self, user_id: str, reason: str = "security_change"):
        """
        Invalida tokens por cambios de seguridad.
        Nota: En nuestra implementación actual usamos permission versioning,
        pero este método está disponible para casos especiales.
        
        Args:
            user_id: ID del usuario
            reason: Razón del cambio de seguridad
        """
        # Por ahora, incrementamos perm_version que ya manejamos
        # En el futuro podríamos mantener un registro de tokens activos
        from ..repositories.users_repo import UsersRepo
        
        users_repo = UsersRepo(current_app.mongo_db)
        users_repo.increment_perm_version(user_id)
        
        current_app.logger.info(f"Invalidated tokens for user {user_id} due to {reason}")
    
    def get_user_blacklist_history(self, user_id: str, limit: int = 20):
        """
        Obtiene el historial de tokens invalidados de un usuario.
        Útil para auditoría y debugging.
        
        Args:
            user_id: ID del usuario
            limit: Límite de resultados
            
        Returns:
            Lista de tokens blacklisted con metadata
        """
        tokens = self.repo.get_blacklisted_tokens_by_user(user_id, limit)
        
        # Formatear para respuesta API
        formatted = []
        for token in tokens:
            formatted.append({
                "jti": token["jti"],
                "blacklisted_at": token["blacklisted_at"].isoformat(),
                "expires_at": token["expires_at"].isoformat(),
                "reason": token["reason"]
            })
        
        return formatted
    
    def cleanup_and_get_stats(self):
        """
        Limpia tokens expirados y obtiene estadísticas.
        Útil para mantenimiento y monitoreo.
        
        Returns:
            Diccionario con estadísticas de limpieza
        """
        cleaned_count = self.repo.cleanup_expired_tokens()
        stats = self.repo.get_stats()
        
        return {
            "cleaned_expired_tokens": cleaned_count,
            "current_stats": stats
        }
