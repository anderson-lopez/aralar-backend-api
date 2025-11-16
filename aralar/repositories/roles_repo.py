from typing import List, Dict, Any
from bson import ObjectId


class RolesRepo:
    def __init__(self, db):
        self.roles = db["roles"]
        self.permissions = db["permissions"]

    def upsert_role(self, name: str, permissions: List[str], description: str = ""):
        self.roles.update_one(
            {"name": name},
            {
                "$set": {
                    "permissions": sorted(set(permissions)),
                    "description": description,
                }
            },
            upsert=True,
        )

    def get_role(self, name: str):
        return self.roles.find_one({"name": name})

    def list_roles(self):
        return list(self.roles.find({}))

    def upsert_permission(self, name: str, description: str = ""):
        self.permissions.update_one(
            {"name": name}, {"$set": {"description": description}}, upsert=True
        )

    def list_permissions(self):
        return list(self.permissions.find({}))

    def list_roles_paginated(self, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """List roles with pagination, ordered by name."""
        return list(self.roles.find({}).skip(skip).limit(limit).sort("name", 1))

    def count_roles(self) -> int:
        return self.roles.count_documents({})

    def list_permissions_paginated(self, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """List permissions with pagination, ordered by name."""
        return list(self.permissions.find({}).skip(skip).limit(limit).sort("name", 1))

    def count_permissions(self) -> int:
        return self.permissions.count_documents({})

    def update_permission_by_id(self, permission_id: str, description: str = ""):
        """Update permission by ObjectId instead of name"""
        try:
            object_id = ObjectId(permission_id)
            result = self.permissions.update_one(
                {"_id": object_id}, {"$set": {"description": description}}
            )
            if result.matched_count == 0:
                return None
            # Return the updated document
            return self.permissions.find_one({"_id": object_id})
        except Exception:
            # Invalid ObjectId format
            return None

    def resolve_roles(self, role_names: List[str]):
        cur = self.roles.find({"name": {"$in": role_names}})
        return list(cur)

    def delete_role(self, name: str) -> int:
        res = self.roles.delete_one({"name": name})
        return res.deleted_count
