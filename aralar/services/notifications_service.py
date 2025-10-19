from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from werkzeug.exceptions import abort
from zoneinfo import ZoneInfo
from aralar.config import BaseConfig as Config


class NotificationsService:
    """Service for notifications business logic"""
    
    def __init__(self, repo):
        self.repo = repo
    
    def create_notification(self, data: Dict[str, Any], tzname: Optional[str] = None) -> str:
        """Create a new notification with validation"""
        # Validate that name is unique
        existing = self.repo.find_by_name(data["name"])
        if existing:
            abort(400, description="Notification name already exists")
        
        # Ensure i18n presence and default locale content
        i18n = data.get("i18n") or {}
        default_locale = i18n.get("default_locale")
        if not default_locale:
            abort(400, description="i18n.default_locale is required")
        # guarantee i18n.locales includes default
        locales_list = set((i18n.get("locales") or []))
        if default_locale not in locales_list:
            locales_list.add(default_locale)
            i18n["locales"] = list(locales_list)
            data["i18n"] = i18n
        # Ensure locales mapping has default locale content
        locales_map = data.get("locales") or {}
        default_has_content = bool((locales_map.get(default_locale) or {}).get("data", {}).get("content"))
        if not default_has_content:
            abort(400, description="locales[default_locale].data.content is required")

        tz = tzname or Config.TENANT_TIMEZONE
        sched = data.get("scheduling", {})
        for k in ("start_date", "end_date"):
            if k in sched and sched[k]:
                dt = sched[k]
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(tz))
                sched[k] = dt.astimezone(timezone.utc).replace(tzinfo=None)

        # Add timestamps
        now = datetime.utcnow()
        notification_data = {
            **data,
            "created_at": now,
            "updated_at": now
        }
        
        return self.repo.insert_one(notification_data)
    
    def get_notification_by_id(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """Get notification by ID"""
        notification = self.repo.find_by_id(notification_id)
        if not notification:
            abort(404, description="Notification not found")
        return notification
    
    def update_notification(self, notification_id: str, data: Dict[str, Any], tzname: Optional[str] = None) -> bool:
        """Update notification with validation"""
        # Check if notification exists
        existing = self.repo.find_by_id(notification_id)
        if not existing:
            abort(404, description="Notification not found")
        
        # If name is being updated, check for uniqueness
        if "name" in data and data["name"] != existing.get("name"):
            name_exists = self.repo.find_by_name(data["name"])
            if name_exists:
                abort(400, description="Notification name already exists")
        
        tz = tzname or Config.TENANT_TIMEZONE
        sched = data.get("scheduling", {})
        for k in ("start_date", "end_date"):
            if k in sched and sched[k]:
                dt = sched[k]
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo(tz))
                sched[k] = dt.astimezone(timezone.utc).replace(tzinfo=None)

        # Add update timestamp
        data["updated_at"] = datetime.utcnow()
        
        return self.repo.update_one(notification_id, data)
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete notification"""
        if not self.repo.find_by_id(notification_id):
            abort(404, description="Notification not found")
        
        return self.repo.delete_one(notification_id)
    
    def get_active_notifications(self, current_time: datetime = None, tzname: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notifications that should be active now"""
        return self.repo.find_active_notifications(current_time, tzname)
    
    def get_all_notifications(self, 
                            location: str = None, 
                            is_active: bool = None,
                            priority_min: int = None,
                            priority_max: int = None) -> List[Dict[str, Any]]:
        """Get all notifications with optional filters"""
        filters = {}
        
        if location:
            filters["display.location"] = location
        
        if is_active is not None:
            filters["is_active"] = is_active
        
        if priority_min is not None or priority_max is not None:
            priority_filter = {}
            if priority_min is not None:
                priority_filter["$gte"] = priority_min
            if priority_max is not None:
                priority_filter["$lte"] = priority_max
            filters["priority"] = priority_filter
        
        return self.repo.find_all(filters)
    
    def toggle_notification_status(self, notification_id: str) -> bool:
        """Toggle notification active status"""
        notification = self.repo.find_by_id(notification_id)
        if not notification:
            abort(404, description="Notification not found")
        
        new_status = not notification.get("is_active", False)
        return self.repo.update_activation_status(notification_id, new_status)
    
    def update_locale(self, notification_id: str, locale: str, data: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> bool:
        """Create or update locale-specific content for a notification"""
        notification = self.repo.find_by_id(notification_id)
        if not notification:
            abort(404, description="Notification not found")
        locales = notification.get("locales", {}) or {}
        locales[locale] = {"data": data, "meta": meta}
        update_doc = {"locales": locales, "updated_at": datetime.utcnow()}
        return self.repo.update_one(notification_id, update_doc)
    
    def get_notifications_by_location(self, location: str) -> List[Dict[str, Any]]:
        """Get notifications by display location"""
        return self.repo.find_by_location(location)
    
    def get_expired_notifications(self, tzname: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notifications that have expired"""
        return self.repo.find_expired_notifications(None, tzname)
    
    def get_upcoming_notifications(self, tzname: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get notifications that will start in the future"""
        return self.repo.find_upcoming_notifications(None, tzname)
    
    def validate_notification_data(self, data: Dict[str, Any]) -> None:
        """Validate notification data for business rules"""
        # Validate scheduling dates
        scheduling = data.get("scheduling", {})
        start_date = scheduling.get("start_date")
        end_date = scheduling.get("end_date")
        
        if start_date and end_date:
            if end_date < start_date:
                abort(400, description="End date must be after or equal to start date")
        
        # Validate time constraints
        time_start = scheduling.get("time_start")
        time_end = scheduling.get("time_end")
        
        if time_start and time_end and start_date and end_date:
            # Check if it's the same day
            if start_date.date() == end_date.date():
                # Same day: time_end must be after time_start
                try:
                    start_time = datetime.strptime(time_start, '%H:%M').time()
                    end_time = datetime.strptime(time_end, '%H:%M').time()
                    
                    if end_time <= start_time:
                        abort(400, description="Time end must be after time start when scheduling is on the same day")
                except ValueError:
                    abort(400, description="Invalid time format")
        
        # Validate i18n only when present (create path requires it via schema)
        i18n = data.get("i18n")
        if i18n is not None:
            default_locale = i18n.get("default_locale")
            if not default_locale:
                abort(400, description="i18n.default_locale is required")
            # If locales map is provided in payload, ensure default locale has content
            locales_map = data.get("locales")
            if locales_map is not None:
                default_has = bool((locales_map.get(default_locale) or {}).get("data", {}).get("content"))
                if not default_has:
                    abort(400, description="locales[default_locale].data.content is required")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        all_notifications = self.repo.find_all()
        active_count = len([n for n in all_notifications if n.get("is_active", False)])
        expired_count = len(self.repo.find_expired_notifications())
        upcoming_count = len(self.repo.find_upcoming_notifications())
        
        return {
            "total": len(all_notifications),
            "active": active_count,
            "expired": expired_count,
            "upcoming": upcoming_count,
            "inactive": len(all_notifications) - active_count
        }
