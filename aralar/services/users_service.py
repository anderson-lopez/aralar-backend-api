from argon2 import PasswordHasher
from datetime import datetime

ph = PasswordHasher()


class UsersService:
    def __init__(self, repo):
        self.repo = repo

    def create_user(self, data: dict):
        """Create a new user with hashed password"""
        # Verificar que el email no exista (validación de negocio)
        existing_user = self.repo.find_by_email(data["email"])
        if existing_user:
            raise ValueError("Email already exists")
        
        # Crear el usuario
        hashed = ph.hash(data.pop("password"))
        doc = {
            **data,
            "password_hash": hashed,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "roles": data.get("roles", []),
        }
        return self.repo.insert(doc)

    
    
    def change_password(self, user_id: str, data: dict):
        """Change user password"""
        user = self.repo.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if not ph.verify(user["password_hash"], data["old_password"]):
            raise ValueError("Old password is incorrect")
        
        hashed = ph.hash(data["new_password"])
        self.repo.update(user_id, {"password_hash": hashed})
        return True
    
    def verify_credentials(self, email, password):
        user = self.repo.find_by_email(email)
        if not user or not user.get("password_hash"):
            return None
        try:
            ph.verify(user["password_hash"], password)
            return user
        except Exception:
            return None
