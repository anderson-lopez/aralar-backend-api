"""
Tests del módulo de notificaciones.

Referencias:
- Blueprint: `aralar/api/notifications/blueprint.py`
- Service:   `aralar/services/notifications_service.py`
- Repo:      `aralar/repositories/notifications_repo.py`
- Guía:      `NOTIFICATIONS_API_GUIDE.md`
"""
import pytest


@pytest.mark.integration
class TestNotificationsService:
    """
    TODO (junior):
    - test_creates_notification_with_default_unread_status
    - test_marks_notification_as_read
    - test_lists_notifications_by_user
    - test_filters_unread_notifications
    """
    pass


@pytest.mark.e2e
class TestNotificationsEndpoints:
    """
    TODO (junior):
    - test_list_returns_401_without_token
    - test_list_returns_current_user_notifications
    - test_mark_as_read_updates_status
    - test_mark_as_read_returns_404_when_notification_not_owned_by_user
    """
    pass
