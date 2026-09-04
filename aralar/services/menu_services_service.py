from typing import Optional


class MenuServicesService:
    """Lógica de negocio del catálogo de servicios de menú.

    Un servicio clasifica menús para la sección pública "Otros servicios".
    El `slug` es la clave estable que referencian los menús (`service_slugs`);
    es único por tenant.
    """

    def __init__(self, repo):
        self.repo = repo

    def create(self, data: dict):
        tenant_id = data["tenant_id"]
        slug = self._normalize_slug(data.get("slug"))
        if not slug:
            return {"error": "slug is required"}
        if self.repo.get_by_slug(tenant_id, slug):
            return {"conflict": "service slug already exists for tenant"}
        doc = {
            "tenant_id": tenant_id,
            "slug": slug,
            "name": data["name"],
            "labels": data.get("labels") or {},
            "order": data.get("order", 0),
            "is_active": data.get("is_active", True),
        }
        _id = self.repo.insert(doc)
        return self.repo.get(_id)

    def get(self, service_id: str):
        return self.repo.get(service_id)

    def list(self, query_args: dict):
        filters: dict = {}
        tenant_id = query_args.get("tenant_id")
        is_active = query_args.get("is_active")
        if tenant_id:
            filters["tenant_id"] = tenant_id
        if is_active is not None:
            filters["is_active"] = is_active
        items = self.repo.list(filters)
        return {"items": items, "total": len(items)}

    def update(self, service_id: str, payload: dict, menus_repo=None):
        """Actualiza un servicio.

        **El `slug` es inmutable** y por eso no está en `allowed`: los menús lo
        referencian como texto en `service_slugs` y no hay cascada, así que
        renombrarlo dejaría esos menús huérfanos (fuera de `/public/available`
        por estar clasificados, y fuera de `/public/services/<slug>` por no
        coincidir el slug). Lo visible en la landing es `labels`/`name`, que sí
        se editan libremente.

        Al **desactivar** (`is_active: False`) un servicio con menús, la
        respuesta incluye `affected_menus` (cuántos quedan ocultos) para que el
        panel pueda avisar. No se bloquea: apagar temporalmente es legítimo.
        """
        m = self.repo.get(service_id)
        if not m:
            return None
        allowed = ("name", "labels", "order", "is_active")
        patch = {k: v for k, v in payload.items() if k in allowed}
        if not patch:
            return m
        res = self.repo.update(service_id, patch)
        if menus_repo is not None and patch.get("is_active") is False:
            count = self._count_referencing_menus(menus_repo, m)
            if count:
                res = dict(res)
                res["affected_menus"] = count
        return res

    @staticmethod
    def _count_referencing_menus(menus_repo, service: dict) -> int:
        return menus_repo.count(
            {"tenant_id": service.get("tenant_id"), "service_slugs": service.get("slug")}
        )

    def delete(self, service_id: str, menus_repo=None):
        """Elimina un servicio. Bloquea (409) si algún menú lo referencia.

        `menus_repo` es opcional para poder testear el service aislado; el
        blueprint siempre lo pasa para hacer la comprobación de referencias.
        """
        m = self.repo.get(service_id)
        if not m:
            return None
        if menus_repo is not None:
            count = self._count_referencing_menus(menus_repo, m)
            if count > 0:
                return {"conflict": f"service is referenced by {count} menu(s)"}
        self.repo.delete(service_id)
        return {"ok": True}

    def public_list(self, tenant_id: Optional[str] = None, locale: Optional[str] = None):
        """Servicios activos para la sección "Otros servicios", ordenados por `order`."""
        items = self.repo.find_active(tenant_id=tenant_id)
        return {"items": [self._to_public(s, locale) for s in items]}

    @staticmethod
    def _to_public(s: dict, locale: Optional[str] = None):
        labels = s.get("labels") or {}
        label = labels.get(locale) if locale else None
        if not label:
            # Cae al primer label disponible o, en su defecto, al nombre interno.
            label = next(iter(labels.values()), None) or s.get("name")
        return {
            "slug": s.get("slug"),
            "name": s.get("name"),
            "label": label,
            "order": s.get("order", 0),
        }

    @staticmethod
    def _normalize_slug(slug) -> str:
        if not slug:
            return ""
        return str(slug).strip().lower().replace(" ", "-")
