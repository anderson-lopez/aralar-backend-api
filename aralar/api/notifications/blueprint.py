from flask_smorest import Blueprint
from marshmallow import ValidationError

from .controllers import (
    create_notification,
    get_notification,
    update_notification,
    delete_notification,
    get_all_notifications,
    get_active_notifications,
    toggle_notification_status,
    get_notifications_by_location,
    get_notification_stats,
    get_expired_notifications,
    get_upcoming_notifications
)
from aralar.schemas.notification_schemas import (
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationOutSchema,
    NotificationListResponseSchema,
    NotificationCreateResponseSchema
)

# Create blueprint
blp = Blueprint("notifications", __name__, description="Notifications API")

# Register routes
@blp.route("/", methods=["POST"])
@blp.arguments(NotificationCreateSchema)
@blp.response(201, NotificationCreateResponseSchema)
@blp.doc(summary="Create notification", description="Create a new notification")
def create_notification_route(data):
    """Create a new notification"""
    return create_notification(data)


@blp.route("/<string:notification_id>", methods=["GET"])
@blp.response(200, NotificationOutSchema)
@blp.doc(summary="Get notification", description="Get notification by ID")
def get_notification_route(notification_id):
    """Get notification by ID"""
    return get_notification(notification_id)


@blp.route("/<string:notification_id>", methods=["PUT"])
@blp.arguments(NotificationUpdateSchema)
@blp.doc(summary="Update notification", description="Update notification by ID")
def update_notification_route(data, notification_id):
    """Update notification"""
    return update_notification(notification_id, data)


@blp.route("/<string:notification_id>", methods=["DELETE"])
@blp.doc(summary="Delete notification", description="Delete notification by ID")
def delete_notification_route(notification_id):
    """Delete notification"""
    return delete_notification(notification_id)


@blp.route("/", methods=["GET"])
@blp.response(200, NotificationListResponseSchema)
@blp.doc(
    summary="Get all notifications", 
    description="Get all notifications with optional filters",
    parameters=[
        {
            "name": "location",
            "in": "query",
            "description": "Filter by display location",
            "required": False,
            "schema": {"type": "string"}
        },
        {
            "name": "is_active",
            "in": "query", 
            "description": "Filter by active status",
            "required": False,
            "schema": {"type": "boolean"}
        },
        {
            "name": "priority_min",
            "in": "query",
            "description": "Minimum priority",
            "required": False,
            "schema": {"type": "integer"}
        },
        {
            "name": "priority_max",
            "in": "query",
            "description": "Maximum priority",
            "required": False,
            "schema": {"type": "integer"}
        }
    ]
)
def get_all_notifications_route():
    """Get all notifications with optional filters"""
    return get_all_notifications()


@blp.route("/active", methods=["GET"])
@blp.doc(
    summary="Get active notifications", 
    description="Get currently active notifications (public endpoint)"
)
def get_active_notifications_route():
    """Get currently active notifications (public endpoint)"""
    return get_active_notifications()


@blp.route("/<string:notification_id>/toggle", methods=["POST"])
@blp.doc(summary="Toggle notification status", description="Toggle notification active status")
def toggle_notification_status_route(notification_id):
    """Toggle notification active status"""
    return toggle_notification_status(notification_id)


@blp.route("/location/<string:location>", methods=["GET"])
@blp.response(200, NotificationListResponseSchema)
@blp.doc(summary="Get notifications by location", description="Get notifications by display location")
def get_notifications_by_location_route(location):
    """Get notifications by display location"""
    return get_notifications_by_location(location)


@blp.route("/stats", methods=["GET"])
@blp.doc(summary="Get notification statistics", description="Get notification statistics")
def get_notification_stats_route():
    """Get notification statistics"""
    return get_notification_stats()


@blp.route("/expired", methods=["GET"])
@blp.response(200, NotificationListResponseSchema)
@blp.doc(summary="Get expired notifications", description="Get notifications that have expired")
def get_expired_notifications_route():
    """Get expired notifications"""
    return get_expired_notifications()


@blp.route("/upcoming", methods=["GET"])
@blp.response(200, NotificationListResponseSchema)
@blp.doc(summary="Get upcoming notifications", description="Get notifications that will start in the future")
def get_upcoming_notifications_route():
    """Get upcoming notifications"""
    return get_upcoming_notifications()