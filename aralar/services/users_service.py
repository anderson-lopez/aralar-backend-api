from argon2 import PasswordHasher
from datetime import datetime

ph = PasswordHasher()


class UsersService:
    def __init__(self, repo):
        self.repo = repo

    def create_user(self, data: dict):
        """Create a new user with comprehensive validation and hashed password"""
        # Validar que las contraseñas coincidan
        if data.get("password") != data.get("confirm_password"):
            raise ValueError("Passwords do not match")
        
        # Verificar que el email no exista
        existing_user = self.repo.find_by_email(data["email"])
        if existing_user:
            raise ValueError("Email already exists")
        
        # Validar formato de email
        if not data.get("email") or "@" not in data["email"]:
            raise ValueError("Invalid email format")
        
        # Validar longitud de contraseña
        if len(data.get("password", "")) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Validar seguridad de contraseña (mayúscula, minúscula, número)
        password = data.get("password", "")
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one number")
        
        # Validar que tenga nombre completo
        if not data.get("full_name") or len(data["full_name"].strip()) < 1:
            raise ValueError("Full name is required")
        
        if len(data["full_name"]) > 50:
            raise ValueError("Full name must be 50 characters or less")
        
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
        if data["new_password"] != data["confirm_new_password"]:
            raise ValueError("New passwords do not match")
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
