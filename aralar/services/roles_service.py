class RolesService:
    def __init__(self, repo):
        self.repo = repo

    # Roles
    def list_roles(self):
        return self.repo.list_roles()

    def get_role(self, name: str):
        return self.repo.get_role(name)

    def create_role(self, data: dict):
        name = data.get("name")
        if not name:
            raise ValueError("name is required")
        # if exists, conflict
        if self.repo.get_role(name):
            return {"conflict": "role already exists"}
        self.repo.upsert_role(
            name=name,
            permissions=data.get("permissions", []),
            description=data.get("description", ""),
        )
        return self.repo.get_role(name)

    def update_role(self, name: str, data: dict):
        if not self.repo.get_role(name):
            return None
        self.repo.upsert_role(
            name=name,
            permissions=data.get("permissions", []),
            description=data.get("description", ""),
        )
        return self.repo.get_role(name)

    def delete_role(self, name: str) -> int:
        return self.repo.delete_role(name)

    # Permissions catalog
    def list_permissions(self):
        return self.repo.list_permissions()

    def upsert_permission(self, name: str, data: dict):
        self.repo.upsert_permission(name=name, description=data.get("description", ""))
        # return the permission document shape
        return {"name": name, "description": data.get("description", "")}

    def update_permission_by_id(self, permission_id: str, data: dict):
        """Update permission by ID instead of name (safer for names with special characters)"""
        return self.repo.update_permission_by_id(
            permission_id=permission_id, description=data.get("description", "")
        )
