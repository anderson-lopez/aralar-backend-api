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
                return {
                    "conflict": f"Template with slug '{slug}' and version {version} already exists"
                }

        try:
            return self.repo.insert(data)
        except ValueError as e:
            return {"conflict": str(e)}

    def duplicate(self, template_id: str, slug: str | None = None, name: str | None = None):
        """Duplica un template como un nuevo **draft** con slug derivado.

        Copia la estructura (``sections``, ``ui``, ``i18n``) y resetea el
        estado: ``status`` → ``draft``, ``version`` → ``1`` y limpia
        ``publish_notes``. Duplicar NO es versionar: genera un template nuevo
        con su propio slug.

        - Si ``slug`` no se pasa, se deriva ``"<slug>-copy"`` resolviendo
          colisiones (``-copy-2``, ``-copy-3``, …).
        - Si se pasa ``slug`` explícito y ya existe (version 1), devuelve
          ``{"conflict": ...}``.

        Devuelve el nuevo ``_id`` (str), ``None`` si el original no existe, o
        ``{"conflict": ...}`` ante colisión de slug.
        """
        t = self.repo.get(template_id)
        if not t:
            return None

        new_doc = deepcopy(t)
        new_doc.pop("_id", None)
        new_doc.pop("created_at", None)
        new_doc.pop("updated_at", None)
        new_doc["status"] = "draft"
        new_doc["version"] = 1
        new_doc["publish_notes"] = ""
        new_doc["name"] = name or f"{t.get('name', '')} (copia)".strip()

        if slug:
            if self.repo.get_by_slug_version(slug, 1):
                return {"conflict": f"Template with slug '{slug}' and version 1 already exists"}
            new_doc["slug"] = slug
        else:
            new_doc["slug"] = self._derive_copy_slug(t["slug"])

        return self.repo.insert(new_doc)

    def _derive_copy_slug(self, base_slug: str) -> str:
        """Devuelve un slug ``<base>-copy`` que no esté en uso por ningún
        template (cualquier versión). Si ya existe, prueba ``<base>-copy-2``,
        ``<base>-copy-3``, … hasta encontrar uno libre."""
        candidate = f"{base_slug}-copy"
        if not self.repo.list({"slug": candidate}, limit=1):
            return candidate
        n = 2
        while self.repo.list({"slug": f"{candidate}-{n}"}, limit=1):
            n += 1
        return f"{candidate}-{n}"

    def list(self, status=None, slug=None, tenant_id=None, skip=0, limit=20):
        f = {}
        if status:
            f["status"] = status
        if slug:
            f["slug"] = slug
        if tenant_id:
            f["tenant_id"] = tenant_id

        items = self.repo.list(f, skip=skip, limit=limit)
        total = self.repo.count(f)

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }

    def get(self, template_id: str):
        return self.repo.get(template_id)

    # Campos de identidad: nunca se actualizan por `update_draft`.
    # `slug`/`version` son la coordenada por la que los menús referencian la
    # plantilla (`template_slug`/`template_version`, sin cascada): cambiarlos
    # dejaría esos menús huérfanos (perderían el manifest `ui` en /render y
    # `delete_template` dejaría de contarlos). `status` tiene sus propios
    # endpoints (publish/unpublish/archive). El schema HTTP ya los rechaza con
    # 422; esto lo garantiza también para llamadas directas al service.
    _IMMUTABLE_FIELDS = ("_id", "slug", "version", "tenant_id", "status")

    def update_draft(self, template_id: str, patch: dict):
        t = self.repo.get(template_id)
        if not t:
            return None
        if t.get("status") != "draft":
            # Señalizamos conflicto sin usar códigos HTTP aquí
            return {"conflict": "only draft templates can be updated"}
        patch = {k: v for k, v in patch.items() if k not in self._IMMUTABLE_FIELDS}
        if not patch:
            return template_id
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
                return {
                    "conflict": f"Another template with slug '{t['slug']}' and version {current_ver} already exists"
                }

            self.repo.update(template_id, {"status": "published", "publish_notes": notes or ""})
            return template_id

    def unpublish(self, template_id: str):
        t = self.repo.get(template_id)
        if not t:
            return None
        if t.get("status") != "published":
            # Solo se permite hacer unpublish de plantillas publicadas
            return {"conflict": "only published templates can be unpublished"}
        self.repo.update(template_id, {"status": "draft"})
        return template_id

    def unarchive(self, template_id: str):
        """Restore an archived template back to draft status.
        
        Args:
            template_id: ID of the template to unarchive
            
        Returns:
            template_id if successful, None if not found, or dict with conflict message
        """
        t = self.repo.get(template_id)
        if not t:
            return None
        if t.get("status") != "archived":
            return {"conflict": "only archived templates can be unarchived"}
        self.repo.update(template_id, {"status": "draft"})
        return template_id

    def delete_template(self, template_id: str, menus_repo):
        """Delete a template after validating no menus are using it.
        
        Args:
            template_id: ID of the template to delete
            menus_repo: MenusRepo instance to check for associated menus
            
        Returns:
            template_id if successful, None if not found, or dict with conflict message
        """
        t = self.repo.get(template_id)
        if not t:
            return None
        
        # Check if any menus are using this template
        menus_count = menus_repo.count_by_template(t["slug"], t["version"])
        
        if menus_count > 0:
            return {
                "conflict": f"Cannot delete template: {menus_count} menu(s) are using this template (slug: '{t['slug']}', version: {t['version']})"
            }
        
        # Safe to delete - no menus are using this template
        deleted_count = self.repo.delete(template_id)
        if deleted_count == 0:
            return {"conflict": "Failed to delete template"}
        
        return template_id
