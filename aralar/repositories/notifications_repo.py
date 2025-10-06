from typing import List, Dict, Any, Optional
from datetime import datetime
from .base_repo import BaseRepository


class NotificationsRepository(BaseRepository):
    """Repository for notifications operations"""
    
    def __init__(self, db):
        # Llamar al constructor del padre para inicializar la coleccion correctamente
        super().__init__("notifications")
        # Sobrescribir con la instancia de db pasada
        self.collection = db["notifications"]
    
    def find_active_notifications(self, current_time: datetime = None) -> List[Dict[str, Any]]:
        """
        Find notifications that should be active at the given time.
        If no time is provided, uses current UTC time.
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        # Get current day of week (0=Monday, 6=Sunday)
        current_day = current_time.weekday()
        day_mapping = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI', 5: 'SAT', 6: 'SUN'}
        current_day_str = day_mapping[current_day]
        current_time_str = current_time.strftime('%H:%M')
        
        # Build query for active notifications
        query = {
            "is_active": True,
            "scheduling.start_date": {"$lte": current_time},
            "scheduling.end_date": {"$gte": current_time},
            "$or": [
                # No days specified (all days)
                {"scheduling.days_of_week": {"$exists": False}},
                {"scheduling.days_of_week": {"$size": 0}},
                # Current day is in the list
                {"scheduling.days_of_week": current_day_str}
            ]
        }
        
        # Get all candidate notifications
        candidates = list(self.collection.find(query).sort("priority", -1))
        
        # Filter by time range if specified
        active_notifications = []
        for notification in candidates:
            scheduling = notification.get('scheduling', {})
            time_start = scheduling.get('time_start')
            time_end = scheduling.get('time_end')
            
            # If no time constraints, include the notification
            if not time_start and not time_end:
                active_notifications.append(notification)
                continue
            
            # If only one time is specified, skip time validation
            if not time_start or not time_end:
                active_notifications.append(notification)
                continue
            
            # Validate time range
            if time_start <= current_time_str <= time_end:
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
        return list(self.collection.find({
            "priority": {"$gte": min_priority, "$lte": max_priority}
        }))
    
    def update_activation_status(self, notification_id: str, is_active: bool) -> bool:
        """Update notification activation status"""
        return self.update_one(notification_id, {"is_active": is_active})
    
    def find_expired_notifications(self, current_time: datetime = None) -> List[Dict[str, Any]]:
        """Find notifications that have expired"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        return list(self.collection.find({
            "scheduling.end_date": {"$lt": current_time}
        }))
    
    def find_upcoming_notifications(self, current_time: datetime = None) -> List[Dict[str, Any]]:
        """Find notifications that will start in the future"""
        if current_time is None:
            current_time = datetime.utcnow()
        
        return list(self.collection.find({
            "scheduling.start_date": {"$gt": current_time}
        }).sort("scheduling.start_date", 1))
