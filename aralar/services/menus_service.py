from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask_smorest import abort
from copy import deepcopy


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

    def update_locale(self, menu_id: str, locale: str, data: dict):
        m = self.repo.get(menu_id)
        if not m:
            return None
        locales = m.get("locales", {})
        locales[locale] = data
        return self.repo.update(menu_id, {"locales": locales})

    def publish_locale(self, menu_id: str, locale: str):
        m = self.repo.get(menu_id)
        if not m:
            return None
        pb = m.get("publish", {})
        pb[locale] = {"status": "published", "published_at": datetime.utcnow().isoformat() + "Z"}
        # Además marcamos el menú como publicado para que aparezca en /public/available
        return self.repo.update(menu_id, {"publish": pb, "status": "published"})

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

    def render(self, menu_id: str, locale: str, fallback: str | None = None):
        m = self.repo.get(menu_id)
        if not m:
            abort(404, message="not found")

        # debe estar publicado en ese locale (o en fallback si lo pediste explícitamente)
        pub = m.get("publish", {})
        if not pub.get(locale) or pub[locale].get("status") != "published":
            # si no hay publicación en locale, se permite usar fallback si viene seteado
            if not fallback:
                abort(409, message=f"menu not published for locale={locale}")

        merged = self._merge_menu(m, locale=locale, fallback=fallback)
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
            "data": merged,
            "published_at": pub.get(locale, {}).get("published_at")
            or (pub.get(fallback, {}).get("published_at") if fallback else None),
            "updated_at": m.get("updated_at"),
        }
        return payload

    def _merge_menu(self, menu_doc: dict, locale: str, fallback: str | None = None) -> dict:
        """Combina common + locales[locale] (o fallback). No muta el original."""
        common = deepcopy(menu_doc.get("common", {}))
        locales = menu_doc.get("locales", {}) or {}
        loc = locales.get(locale) or (locales.get(fallback) if fallback else None)
        if not loc:
            return common  # si no hay traducción, devolvemos solo common

        return self._deep_merge_sections(common, loc)

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
