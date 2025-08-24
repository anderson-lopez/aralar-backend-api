from argon2 import PasswordHasher
from datetime import datetime

ph = PasswordHasher()


class UsersService:
    def __init__(self, repo):
        self.repo = repo

    def create_user(self, data: dict):
        hashed = ph.hash(data.pop("password"))
        doc = {
            **data,
            "password_hash": hashed,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "roles": data.get("roles", []),
        }
        return self.repo.insert(doc)

    def verify_credentials(self, email, password):
        user = self.repo.find_by_email(email)
        if not user or not user.get("password_hash"):
            return None
        try:
            ph.verify(user["password_hash"], password)
            return user
        except Exception:
            return None
