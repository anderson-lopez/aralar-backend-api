from flask import request, current_app
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
from datetime import datetime
from typing import Dict, Any, List, Optional

from aralar.services.notifications_service import NotificationsService
from aralar.repositories.notifications_repo import NotificationsRepository
from aralar.schemas.notification_schemas import (
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationOutSchema,
    NotificationListResponseSchema,
    NotificationCreateResponseSchema
)


def create_notification(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new notification"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        # Validate data with schema
        schema = NotificationCreateSchema()
        validated_data = schema.load(data)
        
        # Additional business validation
        notifications_service.validate_notification_data(validated_data)
        
        # Create notification
        notification_id = notifications_service.create_notification(validated_data)
        
        return {
            "id": notification_id,
            "message": "Notification created successfully"
        }
    except ValidationError as e:
        abort(400, description=f"Validation error: {e.messages}")
    except Exception as e:
        abort(500, description=f"Error creating notification: {str(e)}")


def get_notification(notification_id: str) -> Dict[str, Any]:
    """Get notification by ID"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        notification = notifications_service.get_notification_by_id(notification_id)
        
        # Convert ObjectId to string for JSON serialization
        if notification and "_id" in notification:
            notification["id"] = str(notification["_id"])
            del notification["_id"]
        
        return notification
    except Exception as e:
        abort(500, description=f"Error retrieving notification: {str(e)}")


def update_notification(notification_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update notification"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        # Validate data with schema
        schema = NotificationUpdateSchema()
        validated_data = schema.load(data)
        
        # Additional business validation
        notifications_service.validate_notification_data(validated_data)
        
        # Update notification
        success = notifications_service.update_notification(notification_id, validated_data)
        
        if not success:
            abort(500, description="Failed to update notification")
        
        return {"message": "Notification updated successfully"}
    except ValidationError as e:
        abort(400, description=f"Validation error: {e.messages}")
    except Exception as e:
        abort(500, description=f"Error updating notification: {str(e)}")


def delete_notification(notification_id: str) -> Dict[str, Any]:
    """Delete notification"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        success = notifications_service.delete_notification(notification_id)
        
        if not success:
            abort(500, description="Failed to delete notification")
        
        return {"message": "Notification deleted successfully"}
    except Exception as e:
        abort(500, description=f"Error deleting notification: {str(e)}")


def get_all_notifications() -> Dict[str, Any]:
    """Get all notifications with optional filters"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        # Get query parameters
        location = request.args.get('location')
        is_active = request.args.get('is_active')
        priority_min = request.args.get('priority_min', type=int)
        priority_max = request.args.get('priority_max', type=int)
        
        # Convert is_active string to boolean
        is_active_bool = None
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
        
        # Get notifications
        notifications = notifications_service.get_all_notifications(
            location=location,
            is_active=is_active_bool,
            priority_min=priority_min,
            priority_max=priority_max
        )
        
        # Convert ObjectIds to strings - WORKAROUND for Flask serialization
        for notification in notifications:
            # Extract _id before Flask serializes it
            if "_id" in notification:
                notification["id"] = str(notification["_id"])
                # Don't delete _id yet, let Flask handle it
            else:
                # If no _id, create a dummy id
                notification["id"] = "unknown"
        
        return {
            "items": notifications,
            "total": len(notifications)
        }
    except Exception as e:
        abort(500, description=f"Error retrieving notifications: {str(e)}")


def get_active_notifications() -> List[Dict[str, Any]]:
    """Get currently active notifications (public endpoint)"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        # Optional timezone override, defaults to Config.TENANT_TIMEZONE in service/repo
        tz = request.args.get('tz')
        locale = request.args.get('locale')
        
        notifications = notifications_service.get_active_notifications(tzname=tz)
        
        # Convert ObjectIds to strings and format for public consumption
        formatted_notifications = []
        for notification in notifications:
            try:
                # Pick content by requested locale with fallbacks
                chosen_content: Optional[str] = None
                locales = notification.get("locales", {}) or {}
                i18n = notification.get("i18n") or {}
                default_locale = i18n.get("default_locale")
                if locale and locale in locales:
                    chosen_content = (locales.get(locale) or {}).get("data", {}).get("content")
                if not chosen_content and default_locale and default_locale in locales:
                    chosen_content = (locales.get(default_locale) or {}).get("data", {}).get("content")
                if not chosen_content and locales:
                    # fallback to first available locale
                    first_locale = next(iter(locales.values()))
                    if isinstance(first_locale, dict):
                        chosen_content = (first_locale.get("data") or {}).get("content")
                formatted_notification = {
                    "id": str(notification["_id"]),
                    "content": chosen_content or "",
                    "priority": notification.get("priority", 1),
                    "display": notification.get("display", {})
                }
                formatted_notifications.append(formatted_notification)
            except Exception as e:
                print(f"Error processing notification {notification.get('_id')}: {e}")
                continue
        
        return formatted_notifications
    except Exception as e:
        abort(500, description=f"Error retrieving active notifications: {str(e)}")


def update_notification_locale(notification_id: str, locale: str, data: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Update or create locale-specific content for a notification"""
    try:
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        success = notifications_service.update_locale(notification_id, locale, data, meta)
        if not success:
            abort(500, description="Failed to update notification locale")
        return {"message": "Notification locale updated successfully"}
    except Exception as e:
        abort(500, description=f"Error updating notification locale: {str(e)}")


def toggle_notification_status(notification_id: str) -> Dict[str, Any]:
    """Toggle notification active status"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        success = notifications_service.toggle_notification_status(notification_id)
        
        if not success:
            abort(500, description="Failed to toggle notification status")
        
        return {"message": "Notification status toggled successfully"}
    except Exception as e:
        abort(500, description=f"Error toggling notification status: {str(e)}")


def get_notifications_by_location(location: str) -> Dict[str, Any]:
    """Get notifications by display location"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        notifications = notifications_service.get_notifications_by_location(location)
        
        # Convert ObjectIds to strings
        for notification in notifications:
            if "_id" in notification:
                notification["id"] = str(notification["_id"])
                del notification["_id"]
        
        return {
            "items": notifications,
            "total": len(notifications)
        }
    except Exception as e:
        abort(500, description=f"Error retrieving notifications by location: {str(e)}")


def get_notification_stats() -> Dict[str, Any]:
    """Get notification statistics"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        
        stats = notifications_service.get_notification_stats()
        return stats
    except Exception as e:
        abort(500, description=f"Error retrieving notification stats: {str(e)}")


def get_expired_notifications() -> Dict[str, Any]:
    """Get expired notifications"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        tz = request.args.get('tz')
        
        notifications = notifications_service.get_expired_notifications(tzname=tz)
        
        # Convert ObjectIds to strings
        for notification in notifications:
            if "_id" in notification:
                notification["id"] = str(notification["_id"])
                del notification["_id"]
        
        return {
            "items": notifications,
            "total": len(notifications)
        }
    except Exception as e:
        abort(500, description=f"Error retrieving expired notifications: {str(e)}")


def get_upcoming_notifications() -> Dict[str, Any]:
    """Get upcoming notifications"""
    try:
        # Initialize service
        notifications_repo = NotificationsRepository(current_app.mongo_db)
        notifications_service = NotificationsService(notifications_repo)
        tz = request.args.get('tz')
        
        notifications = notifications_service.get_upcoming_notifications(tzname=tz)
        
        # Convert ObjectIds to strings
        for notification in notifications:
            if "_id" in notification:
                notification["id"] = str(notification["_id"])
                del notification["_id"]
        
        return {
            "items": notifications,
            "total": len(notifications)
        }
    except Exception as e:
        abort(500, description=f"Error retrieving upcoming notifications: {str(e)}")