from argon2 import PasswordHasher
from datetime import datetime
from flask_smorest import abort

ph = PasswordHasher()


class UsersService:
    def __init__(self, repo):
        self.repo = repo

    def list_users(self, skip: int = 0, limit: int = 20):
        """List users with pagination, returning items, total, skip and limit."""
        items = self.repo.list(skip=skip, limit=limit)
        total = self.repo.count()
        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    def create_user(self, data: dict):
        """Create a new user with hashed password"""
        # Verificar que el email no exista (validación de negocio)
        existing_user = self.repo.find_by_email(data["email"])
        if existing_user:
            abort(409, message="Email already exists")

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
            abort(400, message="Old password is incorrect")

        hashed = ph.hash(data["new_password"])
        # Usar el nuevo método que incrementa perm_version automáticamente
        self.repo.change_password(user_id, hashed)
        return True

    def update_user(self, user_id: str, data: dict):
        """Update user profile fields (email, full_name). Validates existence and email uniqueness."""
        user = self.repo.find_by_id(user_id)
        if not user:
            abort(404, message="User not found", error="user_not_found")

        allowed_fields = {"email", "full_name", "roles", "permissions_allow", "permissions_deny"}
        patch = {k: v for k, v in data.items() if k in allowed_fields}

        if not patch:
            abort(400, message="No valid fields to update", error="validation_error")

        if "email" in patch and patch["email"] != user.get("email"):
            existing = self.repo.find_by_email(patch["email"])
            if existing:
                abort(409, message="Email already exists", error="email_conflict")

        patch["updated_at"] = datetime.utcnow()
        return self.repo.update_user(user_id, patch)

    def delete_user(self, user_id: str):
        """Delete a user by ID. Validates existence before deletion."""
        user = self.repo.find_by_id(user_id)
        if not user:
            abort(404, message="User not found", error="user_not_found")
        
        deleted_count = self.repo.delete_user(user_id)
        if deleted_count == 0:
            abort(500, message="Failed to delete user", error="deletion_failed")
        
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
