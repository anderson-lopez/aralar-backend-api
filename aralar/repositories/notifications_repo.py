from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from .base_repo import BaseRepository
from aralar.config import BaseConfig as Config


class NotificationsRepository(BaseRepository):
    """Repository for notifications operations"""

    def __init__(self, db):
        # Llamar al constructor del padre para inicializar la coleccion correctamente
        super().__init__("notifications")
        # Sobrescribir con la instancia de db pasada
        self.collection = db["notifications"]

    def list(
        self, filter_dict: Dict[str, Any] | None = None, skip: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """List notifications with optional filters and pagination."""
        if filter_dict is None:
            filter_dict = {}
        return list(
            self.collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
        )

    def count(self, filter_dict: Dict[str, Any] | None = None) -> int:
        """Count notifications matching optional filters."""
        if filter_dict is None:
            filter_dict = {}
        return self.collection.count_documents(filter_dict)

    def find_active_notifications(
        self, current_time: datetime = None, tzname: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find notifications that should be active at the given time using tenant timezone
        for day-of-week and HH:MM, but UTC for date range in DB.
        """
        tz = tzname or Config.TENANT_TIMEZONE
        tzinfo = ZoneInfo(tz)
        # Determine local now and corresponding UTC naive timestamp
        if current_time is None:
            now_local = datetime.now(tzinfo)
        else:
            # If passed time is naive, assume local tz; if aware, convert to local
            now_local = (
                current_time.replace(tzinfo=tzinfo)
                if current_time.tzinfo is None
                else current_time.astimezone(tzinfo)
            )
        now_utc = now_local.astimezone(timezone.utc).replace(tzinfo=None)

        # Day-of-week and time in local tz
        current_day = now_local.weekday()  # 0=Mon..6=Sun
        day_mapping = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}
        current_day_str = day_mapping[current_day]
        current_time_str = now_local.strftime("%H:%M")

        # Build query for active notifications by UTC date window and optional day filter
        query = {
            "is_active": True,
            "scheduling.start_date": {"$lte": now_utc},
            "scheduling.end_date": {"$gte": now_utc},
            "$or": [
                {"scheduling.days_of_week": {"$exists": False}},
                {"scheduling.days_of_week": {"$size": 0}},
                {"scheduling.days_of_week": current_day_str},
            ],
        }

        candidates = list(self.collection.find(query).sort("priority", -1))

        # Time-of-day filter with overnight window support
        active_notifications = []
        for notification in candidates:
            scheduling = notification.get("scheduling", {})
            time_start = scheduling.get("time_start")
            time_end = scheduling.get("time_end")

            # No time constraints
            if not time_start and not time_end:
                active_notifications.append(notification)
                continue

            # One-side constraint: include
            if not time_start or not time_end:
                active_notifications.append(notification)
                continue

            # Normal window
            if time_start <= time_end:
                if time_start <= current_time_str <= time_end:
                    active_notifications.append(notification)
            else:
                # Overnight window (wrap over midnight)
                if current_time_str >= time_start or current_time_str <= time_end:
                    active_notifications.append(notification)

        return active_notifications

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find notification by name"""
        return self.collection.find_one({"name": name})

    def find_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Find notifications by display location"""
        return list(self.collection.find({"display.location": location}))

    def find_by_priority_range(self, min_priority: int, max_priority: int) -> List[Dict[str, Any]]:
        """Find notifications within priority range"""
        return list(
            self.collection.find({"priority": {"$gte": min_priority, "$lte": max_priority}})
        )

    def update_activation_status(self, notification_id: str, is_active: bool) -> bool:
        """Update notification activation status"""
        return self.update_one(notification_id, {"is_active": is_active})

    def find_expired_notifications(
        self, current_time: datetime = None, tzname: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find notifications that have expired (compare in UTC)"""
        tz = tzname or Config.TENANT_TIMEZONE
        tzinfo = ZoneInfo(tz)
        if current_time is None:
            now_local = datetime.now(tzinfo)
        else:
            now_local = (
                current_time.replace(tzinfo=tzinfo)
                if current_time.tzinfo is None
                else current_time.astimezone(tzinfo)
            )
        now_utc = now_local.astimezone(timezone.utc).replace(tzinfo=None)

        return list(self.collection.find({"scheduling.end_date": {"$lt": now_utc}}))

    def find_upcoming_notifications(
        self, current_time: datetime = None, tzname: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find notifications that will start in the future (compare in UTC)"""
        tz = tzname or Config.TENANT_TIMEZONE
        tzinfo = ZoneInfo(tz)
        if current_time is None:
            now_local = datetime.now(tzinfo)
        else:
            now_local = (
                current_time.replace(tzinfo=tzinfo)
                if current_time.tzinfo is None
                else current_time.astimezone(tzinfo)
            )
        now_utc = now_local.astimezone(timezone.utc).replace(tzinfo=None)

        return list(
            self.collection.find({"scheduling.start_date": {"$gt": now_utc}}).sort(
                "scheduling.start_date", 1
            )
        )
