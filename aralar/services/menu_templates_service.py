from copy import deepcopy


class MenuTemplatesService:
    def __init__(self, repo):
        self.repo = repo

    def create(self, data: dict):
        data.setdefault("status", "draft")
        return self.repo.insert(data)

    def list(self, status=None, slug=None, tenant_id=None):
        f = {}
        if status:
            f["status"] = status
        if slug:
            f["slug"] = slug
        if tenant_id:
            f["tenant_id"] = tenant_id
        return self.repo.list(f)

    def get(self, template_id: str):
        return self.repo.get(template_id)

    def update_draft(self, template_id: str, patch: dict):
        t = self.repo.get(template_id)
        if not t:
            return None
        if t.get("status") != "draft":
            # Señalizamos conflicto sin usar códigos HTTP aquí
            return {"conflict": "only draft templates can be updated"}
        # Evita intentar modificar _id y otros campos no actualizables a nivel de servicio
        if "_id" in patch:
            patch.pop("_id", None)
        return self.repo.update(template_id, patch)

    def publish(self, template_id: str, notes: str | None = None):
        t = self.repo.get(template_id)
        if not t:
            return None
        # clone with version+1 if already published, else publish v=existing or v=1?
        current_ver = t.get("version", 1)
        # Strategy: create NEW document with version = max(slug)+1
        same_slug = self.repo.list({"slug": t["slug"]}, limit=1000, skip=0)
        max_ver = max([x.get("version", 1) for x in same_slug]) if same_slug else current_ver
        new_doc = deepcopy(t)
        new_doc.pop("_id", None)
        new_doc["version"] = max_ver + 1 if t.get("status") == "published" else current_ver
        new_doc["status"] = "published"
        new_doc["publish_notes"] = notes or ""
        return self.repo.insert(new_doc)
