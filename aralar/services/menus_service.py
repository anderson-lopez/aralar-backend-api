from datetime import datetime, timezone
from zoneinfo import ZoneInfo


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
        return self.repo.update(menu_id, {"publish": pb})

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
