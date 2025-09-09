from typing import Dict, Optional
from .users_service import UsersService


class AuthService:
    """Servicio de autenticación simplificado"""
    
    def __init__(self, users_service: UsersService):
        self.users_service = users_service
    
    def register(self, data: dict):
        """Register a new user with default role 'user'"""
        # Preparar datos para crear usuario con rol por defecto
        user_data = {
            "email": data["email"],
            "password": data["password"],
            "confirm_password": data["confirm_password"],
            "full_name": data["full_name"],
            "roles": ["user"]  # Rol por defecto para registro público
        }
        
        # Invocar el método create_user del UsersService (que ya tiene todas las validaciones)
        return self.users_service.create_user(user_data)