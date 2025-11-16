from typing import List
from .base_repo import to_object_id


class UsersRepo:
    def __init__(self, db):
        self.col = db["users"]

    def insert(self, doc: dict):
        res = self.col.insert_one(doc)
        return str(res.inserted_id)

    def find_by_email(self, email: str):
        return self.col.find_one({"email": email})

    def find_by_id(self, _id: str):
        return self.col.find_one({"_id": to_object_id(_id)})

    def update(self, _id: str, patch: dict):
        self.col.update_one({"_id": to_object_id(_id)}, {"$set": patch})
        return self.find_by_id(_id)

    def list(self, filters=None, skip=0, limit=20):
        cur = self.col.find(filters or {}).skip(skip).limit(limit)
        return list(cur)

    def count(self, filters=None) -> int:
        """Count users matching optional filters."""
        return self.col.count_documents(filters or {})

    def set_user_roles(self, _id: str, roles: List[str]):
        self.col.update_one(
            {"_id": to_object_id(_id)}, {"$set": {"roles": roles}, "$inc": {"perm_version": 1}}
        )

    def set_user_permissions(self, _id: str, allow: List[str], deny: List[str]):
        self.col.update_one(
            {"_id": to_object_id(_id)},
            {
                "$set": {"permissions_allow": allow, "permissions_deny": deny},
                "$inc": {"perm_version": 1},
            },
        )

    def deactivate_user(self, _id: str):
        """Desactiva usuario e incrementa perm_version para invalidar tokens"""
        self.col.update_one(
            {"_id": to_object_id(_id)}, {"$set": {"active": False}, "$inc": {"perm_version": 1}}
        )

    def activate_user(self, _id: str):
        """Activa usuario e incrementa perm_version"""
        self.col.update_one(
            {"_id": to_object_id(_id)}, {"$set": {"active": True}, "$inc": {"perm_version": 1}}
        )

    def change_password(self, _id: str, password_hash: str):
        """Cambia contraseña e incrementa perm_version para invalidar tokens"""
        self.col.update_one(
            {"_id": to_object_id(_id)},
            {"$set": {"password": password_hash}, "$inc": {"perm_version": 1}},
        )

    def increment_perm_version(self, _id: str):
        """Incrementa perm_version manualmente para invalidar tokens"""
        self.col.update_one({"_id": to_object_id(_id)}, {"$inc": {"perm_version": 1}})
