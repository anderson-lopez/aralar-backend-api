from argon2 import PasswordHasher
from datetime import datetime
from flask_smorest import abort

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
        data.pop("confirm_password")
        doc = {
            **data,
            "password_hash": hashed,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "roles": data.get("roles", []),
        }
        return self.repo.insert(doc)

    def change_password(self, user_id: str, data: dict):
        """Change user password and increment perm_version to invalidate existing tokens"""
        user = self.repo.find_by_id(user_id)
        if not user:
            abort(404, message="User not found", error="user_not_found")
        if not ph.verify(user["password_hash"], data["old_password"]):
            raise ValueError("Old password is incorrect")

        hashed = ph.hash(data["new_password"])
        # Usar el nuevo método que incrementa perm_version automáticamente
        self.repo.change_password(user_id, hashed)
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
