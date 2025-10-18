from copy import deepcopy


class MenuTemplatesService:
    def __init__(self, repo):
        self.repo = repo

    def create(self, data: dict):
        data.setdefault("status", "draft")
        
        # Validar que no exista un template con el mismo slug+version
        slug = data.get("slug")
        version = data.get("version", 1)
        
        if slug and version:
            existing = self.repo.get_by_slug_version(slug, version)
            if existing:
                return {"conflict": f"Template with slug '{slug}' and version {version} already exists"}
        
        try:
            return self.repo.insert(data)
        except ValueError as e:
            return {"conflict": str(e)}

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
        self.repo.update(template_id, patch)
        return template_id

    def publish(self, template_id: str, notes: str | None = None):
        t = self.repo.get(template_id)
        if not t:
            return None
        
        current_ver = t.get("version", 1)
        
        # Si ya está publicado, crear nueva versión
        if t.get("status") == "published":
            # Buscar la versión más alta para este slug
            same_slug = self.repo.list({"slug": t["slug"]}, limit=1000, skip=0)
            max_ver = max([x.get("version", 1) for x in same_slug]) if same_slug else current_ver
            
            new_doc = deepcopy(t)
            new_doc.pop("_id", None)
            new_doc["version"] = max_ver + 1
            new_doc["status"] = "published"
            new_doc["publish_notes"] = notes or ""
            
            # Validar que la nueva versión no exista
            existing = self.repo.get_by_slug_version(t["slug"], max_ver + 1)
            if existing:
                return {"conflict": f"Version {max_ver + 1} already exists for slug '{t['slug']}'"}
            
            return self.repo.insert(new_doc)
        else:
            # Publicar versión actual (draft -> published)
            # Verificar que no exista ya una versión publicada con mismo slug+version
            existing = self.repo.get_by_slug_version(t["slug"], current_ver)
            if existing and existing.get("_id") != t.get("_id"):
                return {"conflict": f"Another template with slug '{t['slug']}' and version {current_ver} already exists"}
            
            self.repo.update(template_id, {
                "status": "published",
                "publish_notes": notes or ""
            })
            return template_id
