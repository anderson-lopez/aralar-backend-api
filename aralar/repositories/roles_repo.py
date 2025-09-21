from typing import List


class RolesRepo:
    def __init__(self, db):
        self.roles = db["roles"]
        self.permissions = db["permissions"]
        self.roles.create_index("name", unique=True)
        self.permissions.create_index("name", unique=True)

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

    def resolve_roles(self, role_names: List[str]):
        cur = self.roles.find({"name": {"$in": role_names}})
        return list(cur)

    def delete_role(self, name: str) -> int:
        res = self.roles.delete_one({"name": name})
        return res.deleted_count
