from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask_smorest import abort
from copy import deepcopy
from typing import List, Optional


class MenusService:
    def __init__(self, repo, templates_repo):
        self.repo = repo
        self.templates_repo = templates_repo

    def create(self, data: dict):
        # resolve template
        tmpl = None
        if data.get("template_id"):
            tmpl = self.templates_repo.get(data["template_id"])
        elif data.get("template_slug") and data.get("template_version"):
            tmpl = self.templates_repo.get_by_slug_version(
                data["template_slug"], data["template_version"]
            )
        if not tmpl:
            return None

        doc = {
            "tenant_id": data["tenant_id"],
            "template_id": str(tmpl["_id"]),
            "template_slug": tmpl["slug"],
            "template_version": tmpl["version"],
            "status": data.get("status", "draft"),
            "common": data.get("common", {}),
            "locales": data.get("locales", {}),
            "publish": {},
            "featured": data.get("featured", False),
            "featured_order": data.get("featured_order"),
        }
        _id = self.repo.insert(doc)
        return self.repo.get(_id)

    def list(self, filters: dict):
        return self.repo.list(filters)

    def get(self, menu_id: str):
        return self.repo.get(menu_id)

    def update_common(self, menu_id: str, common: dict):
        m = self.repo.get(menu_id)
        if not m:
            return None
        return self.repo.update(menu_id, {"common": common})

    def update_locale(self, menu_id: str, locale: str, data: dict, meta: Optional[dict] = None):
        m = self.repo.get(menu_id)
        if not m:
            return None
        locales = m.get("locales", {})
        locales[locale] = {"data": data, "meta": meta}
        return self.repo.update(menu_id, {"locales": locales})

    def publish_locale(self, menu_id: str, locale: str):
        m = self.repo.get(menu_id)
        if not m:
            return None
        pb = m.get("publish", {})
        pb[locale] = {"status": "published", "published_at": datetime.utcnow().isoformat() + "Z"}
        # Ya no cambiamos el estado global del menú aquí (opción 2)
        return self.repo.update(menu_id, {"publish": pb})

    def validate_menu(self, menu_id: str) -> dict | None:
        """Valida si un menú está listo para publicación global.
        Requisitos mínimos:
          - availability presente y con days_of_week y date_ranges válidos
          - al menos un locale publicado
        Devuelve dict {ok: bool, issues: [str, ...]} o None si no existe.
        """
        m = self.repo.get(menu_id)
        if not m:
            return None
        issues: list[str] = []
        avail = m.get("availability") or {}
        if not avail:
            issues.append("availability is required")
        else:
            if not avail.get("timezone"):
                issues.append("availability.timezone is required")
            if not avail.get("days_of_week"):
                issues.append("availability.days_of_week must be non-empty")
            drs = avail.get("date_ranges") or []
            if not drs:
                issues.append("availability.date_ranges must be non-empty")

        pub = m.get("publish") or {}
        has_any_published_locale = any(
            isinstance(v, dict) and v.get("status") == "published" for v in pub.values()
        )
        if not has_any_published_locale:
            issues.append("at least one locale must be published")

        return {"ok": len(issues) == 0, "issues": issues}

    def publish_menu(self, menu_id: str):
        """Publica globalmente el menú si pasa la validación mínima."""
        m = self.repo.get(menu_id)
        if not m:
            return None
        result = self.validate_menu(menu_id)
        if not result["ok"]:
            return result
        self.repo.update(menu_id, {"status": "published"})
        return {"ok": True, "issues": []}

    def unpublish_menu(self, menu_id: str):
        """Despublica el menú (vuelve a estado draft)."""
        m = self.repo.get(menu_id)
        if not m:
            return None
        return self.repo.update(menu_id, {"status": "draft"})

    @staticmethod
    def _weekday_code(dt_local) -> str:
        # MON..SUN
        return ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][dt_local.weekday()]

    def set_availability(self, menu_id: str, availability: dict):
        # Normaliza date_ranges a ISO strings por coherencia (Mongo guarda Date o string; usa uno)
        norm = {
            "timezone": availability["timezone"],
            "days_of_week": availability["days_of_week"],
            "date_ranges": [
                {"start": dr["start"].isoformat(), "end": dr["end"].isoformat()}
                for dr in availability["date_ranges"]
            ],
        }
        return self.repo.set_availability(menu_id, norm)

    def available_on(self, locale: str, tzname: str, date_utc: datetime):
        """Lista menús disponibles en la fecha/hora dada (usa tz para calcular weekday y date)."""
        tz = ZoneInfo(tzname)
        dt_local = date_utc.astimezone(tz)
        day_iso = dt_local.date().isoformat()
        weekday = self._weekday_code(dt_local)
        return self.repo.list_published_by_day(locale=locale, date_iso=day_iso, weekday=weekday)

    def active_now(self, locale: str, tzname: str):
        return self.available_on(locale=locale, tzname=tzname, date_utc=datetime.now(timezone.utc))

    def update_featured(self, menu_id: str, featured: bool, featured_order: Optional[int] = None):
        """Update featured status and order of a menu"""
        m = self.repo.get(menu_id)
        if not m:
            return None
        
        update_data = {"featured": featured}
        if featured_order is not None:
            update_data["featured_order"] = featured_order
        elif not featured:
            # If unfeaturing, remove the order
            update_data["featured_order"] = None
            
        return self.repo.update(menu_id, update_data)

    def featured_available_on(self, locale: str, tzname: str, date_utc: datetime):
        """Lista menus destacados disponibles en la fecha/hora dada"""
        tz = ZoneInfo(tzname)
        dt_local = date_utc.astimezone(tz)
        day_iso = dt_local.date().isoformat()
        weekday = self._weekday_code(dt_local)
        return self.repo.list_featured_by_day(locale=locale, date_iso=day_iso, weekday=weekday)

    def featured_active_now(self, locale: str, tzname: str):
        """Lista menus destacados disponibles ahora"""
        return self.featured_available_on(locale=locale, tzname=tzname, date_utc=datetime.now(timezone.utc))

    def render_featured_menus(self, locale: str, tzname: str, fallback: Optional[str] = None, date_utc: Optional[datetime] = None, include_ui: bool = False):
        """
        Devuelve lista de menus destacados completamente renderizados para mostrar en landing.
        
        Args:
            locale: Idioma requerido (ej: 'es-ES')
            tzname: Zona horaria (ej: 'Europe/Madrid')
            fallback: Idioma de respaldo opcional
            date_utc: Fecha específica, si no se proporciona usa fecha actual
            include_ui: Si incluir manifest de UI en cada menu
        
        Returns:
            Lista de menus renderizados ordenados por featured_order
        """
        if date_utc is None:
            date_utc = datetime.now(timezone.utc)
            
        # Obtener menus destacados disponibles
        featured_menus = self.featured_available_on(locale=locale, tzname=tzname, date_utc=date_utc)
        
        # Renderizar cada menu
        rendered_menus = []
        for menu in featured_menus:
            try:
                # Verificar que el menu esté publicado en el locale solicitado
                pub = menu.get("publish", {})
                if not pub.get(locale) or pub[locale].get("status") != "published":
                    if not fallback or not pub.get(fallback) or pub[fallback].get("status") != "published":
                        continue  # Skip this menu if not published
                
                # Renderizar el menu
                result = self._merge_menu(menu, locale=locale, fallback=fallback)
                data, meta = result["data"], result["meta"]
                
                rendered_menu = {
                    "id": str(menu["_id"]),
                    "template_slug": menu.get("template_slug"),
                    "template_version": menu.get("template_version"),
                    "title": self.resolve_meta(menu, "title", locale, fallback),
                    "summary": self.resolve_meta(menu, "summary", locale, fallback),
                    "featured_order": menu.get("featured_order"),
                    "updated_at": menu.get("updated_at"),
                    "data": data,
                    "meta": meta,
                }
                
                # Agregar UI manifest si se solicita
                if include_ui:
                    tmpl = self.templates_repo.get_by_slug_version(
                        menu["template_slug"], menu["template_version"]
                    )
                    if tmpl:
                        rendered_menu["ui"] = {
                            "layout": (tmpl.get("ui") or {}).get("layout", "sections"),
                            "sections": [],
                            "catalogs": (tmpl.get("ui") or {}).get("catalogs", {}),
                        }
                        for sec in tmpl.get("sections", []):
                            sec_ui = deepcopy(sec.get("ui", {}))
                            sec_ui["key"] = sec.get("key")
                            sec_ui["labels"] = sec.get("label", {})
                            rendered_menu["ui"]["sections"].append(sec_ui)
                
                rendered_menus.append(rendered_menu)
                
            except Exception as e:
                # Log error but continue with other menus
                print(f"Error rendering featured menu {menu.get('_id')}: {e}")
                continue
        
        # Ordenar por featured_order (None values al final)
        rendered_menus.sort(key=lambda x: (x["featured_order"] is None, x["featured_order"] or 0))
        
        return rendered_menus

    def render_multiple(self, menu_ids: List[str], locale: str, fallback: Optional[str] = None, include_ui: bool = False):
        """
        Renderiza múltiples menus de una vez.
        
        Args:
            menu_ids: Lista de IDs de menus a renderizar
            locale: Idioma requerido
            fallback: Idioma de respaldo opcional
            include_ui: Si incluir manifest de UI
            
        Returns:
            Dict con 'items' (menus renderizados) y 'errors' (errores por menu_id)
        """
        rendered_items = []
        errors = {}
        
        for menu_id in menu_ids:
            try:
                rendered_menu = self.render(menu_id, locale=locale, fallback=fallback, include_ui=include_ui)
                rendered_items.append(rendered_menu)
            except Exception as e:
                errors[menu_id] = str(e)
                continue
        
        result = {"items": rendered_items}
        if errors:
            result["errors"] = errors
            
        return result

    def render(
        self, menu_id: str, locale: str, fallback: Optional[str] = None, include_ui: bool = False
    ):
        m = self.repo.get(menu_id)
        if not m:
            abort(404, message="not found")

        # debe estar publicado en ese locale (o en fallback si lo pediste explícitamente)
        pub = m.get("publish", {})
        if not pub.get(locale) or pub[locale].get("status") != "published":
            # si no hay publicación en locale, se permite usar fallback si viene seteado
            if not fallback:
                abort(409, message=f"menu not published for locale={locale}")

        result = self._merge_menu(m, locale=locale, fallback=fallback)
        data, meta = result["data"], result["meta"]
        payload = {
            "id": str(m["_id"]),
            "tenant_id": m.get("tenant_id"),
            "template": {
                "slug": m.get("template_slug"),
                "version": m.get("template_version"),
            },
            "locale": locale,
            "fallback_used": (
                fallback if (fallback and locale not in m.get("locales", {})) else None
            ),
            "data": data,
            "meta": meta,
            "published_at": pub.get(locale, {}).get("published_at")
            or (pub.get(fallback, {}).get("published_at") if fallback else None),
            "updated_at": m.get("updated_at"),
        }

        if include_ui:
            # Cargar template y construir manifest
            tmpl = self.templates_repo.get_by_slug_version(
                m["template_slug"], m["template_version"]
            )
            if tmpl:
                payload["ui"] = {
                    "layout": (tmpl.get("ui") or {}).get("layout", "sections"),
                    "sections": [],
                    "catalogs": (tmpl.get("ui") or {}).get("catalogs", {}),
                }
                for sec in tmpl.get("sections", []):
                    sec_ui = deepcopy(sec.get("ui", {}))
                    sec_ui["key"] = sec.get("key")
                    sec_ui["labels"] = sec.get("label", {})
                    payload["ui"]["sections"].append(sec_ui)

        return payload

    def _merge_menu(self, menu_doc: dict, locale: str, fallback: Optional[str] = None) -> dict:
        """Combina common + locales[locale] (o fallback). No muta el original."""
        common = deepcopy(menu_doc.get("common", {}))
        locales = menu_doc.get("locales", {}) or {}
        loc = locales.get(locale) or (locales.get(fallback) if fallback else None)
        if not loc:
            return common  # si no hay traducción, devolvemos solo common
        # ¡ojo! tomamos sólo el bloque traducible:
        loc_data = loc.get("data") or {}
        if not loc_data and fallback:
            loc_data = locales.get(fallback, {}).get("data") or {}
        merged = self._deep_merge_sections(common, loc_data)
        meta = self._resolve_meta(menu_doc, locale, fallback)
        return {"data": merged, "meta": meta}

    def _resolve_meta(self, menu_doc: dict, locale: str, fallback: Optional[str] = None) -> dict:
        loc = menu_doc.get("locales", {}).get(locale) or (
            menu_doc.get("locales", {}).get(fallback) if fallback else None
        )
        if not loc:
            return {}
        return loc.get("meta", {})

    def _deep_merge_sections(self, base, override):
        """
        Reglas:
          - dict: fusiona recursivo, override pisa base
          - list con objetos que tienen '_id': mezcla por _id
          - list normal: override pisa base
          - atómico: override si no es None, si no, base
        """
        # list de bloques con _id: merge por _id
        if isinstance(base, list) and all(isinstance(x, dict) and "_id" in x for x in base):
            if not isinstance(override, list):
                return base
            index = {x["_id"]: x for x in base}
            for blk in override:
                bid = blk.get("_id")
                if bid in index:
                    index[bid] = self._deep_merge_sections(index[bid], blk)
                # si aparece un bloque nuevo solo en override: por política, lo ignoramos
            return list(index.values())

        # dict
        if isinstance(base, dict) and isinstance(override, dict):
            res = dict(base)
            for k, v in override.items():
                if k == "_id":
                    continue
                res[k] = self._deep_merge_sections(base.get(k), v)
            return res

        # valores atómicos / listas simples
        return override if override is not None else base

    def resolve_meta(self, m, key, locale, fallback: Optional[str] = None):
        loc = m.get("locales", {})
        return (
            (loc.get(locale, {}).get("meta", {}) or {}).get(key)
            or (loc.get(fallback, {}).get("meta", {}) or {}).get(key)
            or (m.get("common", {}).get("meta", {}) or {}).get(key)
        )
