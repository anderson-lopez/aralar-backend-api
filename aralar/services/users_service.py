from argon2 import PasswordHasher
from datetime import datetime
from flask_smorest import abort

ph = PasswordHasher()


class UsersService:
    def __init__(self, repo):
        self.repo = repo

    def create_user(self, data: dict):
        """Create a new user with comprehensive validation and hashed password"""
        # Validar que las contraseñas coincidan
        if data.get("password") != data.get("confirm_password"):
            abort(400, message="Passwords do not match", error="validation_error")

        # Verificar que el email no exista
        existing_user = self.repo.find_by_email(data["email"])
        if existing_user:
            abort(400, message="Email already exists", error="validation_error")

        # Validar formato de email
        if not data.get("email") or "@" not in data["email"]:
            abort(400, message="Invalid email format", error="validation_error")

        # Validar longitud de contraseña
        if len(data.get("password", "")) < 8:
            abort(
                400, message="Password must be at least 8 characters long", error="validation_error"
            )

        # Validar seguridad de contraseña (mayúscula, minúscula, número)
        password = data.get("password", "")
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not (has_upper and has_lower and has_digit):
            abort(
                400,
                message="Password must contain at least one uppercase letter, one lowercase letter, and one number",
                error="validation_error",
            )

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
            abort(400, message="Old password is incorrect", error="validation_error")
        if data["new_password"] != data["confirm_new_password"]:
            abort(400, message="New passwords do not match", error="validation_error")
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
