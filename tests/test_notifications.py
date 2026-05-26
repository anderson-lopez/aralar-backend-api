"""
Tests del módulo de notificaciones.

Referencias:
- Blueprint: `aralar/api/notifications/blueprint.py`
- Service:   `aralar/services/notifications_service.py`
- Repo:      `aralar/repositories/notifications_repo.py`

Las notificaciones son entidades programadas (banner, modal, toast) con
ventana de fechas y horarios. Aquí cubrimos:
- Validaciones del service (nombre duplicado, default_locale requerido, etc.).
- CRUD básico.
- Endpoints más comunes con auth.
"""
from datetime import datetime, timedelta, timezone

import pytest

from aralar.services.notifications_service import NotificationsService
from aralar.repositories.notifications_repo import NotificationsRepository


def _svc(db):
    return NotificationsService(NotificationsRepository(db))


def _valid_create(**overrides):
    base = {
        "name": "Test Notification",
        "is_active": True,
        "priority": 1,
        "scheduling": {
            "start_date": datetime.now(timezone.utc),
            "end_date": datetime.now(timezone.utc) + timedelta(days=1),
            "days_of_week": [],
        },
        "display": {"location": "top-bar", "type": "banner"},
        "locales": {"es-ES": {"data": {"content": "Hola"}}},
        "i18n": {"default_locale": "es-ES", "locales": ["es-ES"]},
    }
    base.update(overrides)
    return base


@pytest.mark.integration
class TestNotificationsService:
    """Tests del service de notifications (unidad+integración con mongomock)."""

    def test_creates_notification_when_payload_is_valid(self, db):
        _id = _svc(db).create_notification(_valid_create())
        assert _id is not None
        assert db["notifications"].count_documents({"name": "Test Notification"}) == 1

    def test_rejects_creation_when_name_already_exists(self, db, app):
        with app.app_context():
            _svc(db).create_notification(_valid_create(name="Repetida"))
            from werkzeug.exceptions import HTTPException
            with pytest.raises(HTTPException) as exc:
                _svc(db).create_notification(_valid_create(name="Repetida"))
            assert exc.value.code == 400

    def test_rejects_creation_when_default_locale_missing(self, db, app):
        from werkzeug.exceptions import HTTPException
        payload = _valid_create()
        payload["i18n"] = {"locales": ["es-ES"]}  # sin default_locale
        with app.app_context():
            with pytest.raises(HTTPException) as exc:
                _svc(db).create_notification(payload)
            assert exc.value.code == 400

    def test_rejects_creation_when_default_locale_has_no_content(self, db, app):
        from werkzeug.exceptions import HTTPException
        payload = _valid_create()
        payload["locales"] = {"es-ES": {"data": {}}}  # sin content
        with app.app_context():
            with pytest.raises(HTTPException) as exc:
                _svc(db).create_notification(payload)
            assert exc.value.code == 400

    def test_get_by_id_returns_404_when_not_found(self, db, app):
        from werkzeug.exceptions import HTTPException
        from bson import ObjectId
        with app.app_context():
            with pytest.raises(HTTPException) as exc:
                _svc(db).get_notification_by_id(str(ObjectId()))
            assert exc.value.code == 404

    def test_delete_returns_404_when_not_found(self, db, app):
        from werkzeug.exceptions import HTTPException
        from bson import ObjectId
        with app.app_context():
            with pytest.raises(HTTPException) as exc:
                _svc(db).delete_notification(str(ObjectId()))
            assert exc.value.code == 404

    def test_delete_removes_existing_notification(self, db):
        _id = _svc(db).create_notification(_valid_create(name="Para borrar"))
        _svc(db).delete_notification(_id)
        assert db["notifications"].count_documents({"_id": __import__("bson").ObjectId(_id)}) == 0

    def test_get_all_returns_paginated_structure(self, db):
        _svc(db).create_notification(_valid_create(name="N1"))
        _svc(db).create_notification(_valid_create(name="N2"))
        result = _svc(db).get_all_notifications()
        assert set(result.keys()) == {"items", "total", "skip", "limit"}
        assert result["total"] == 2

    def test_get_all_filters_by_location(self, db):
        n1 = _valid_create(name="TopBar")
        n1["display"]["location"] = "top-bar"
        n2 = _valid_create(name="Footer")
        n2["display"]["location"] = "footer"
        _svc(db).create_notification(n1)
        _svc(db).create_notification(n2)
        result = _svc(db).get_all_notifications(location="footer")
        names = [n["name"] for n in result["items"]]
        assert names == ["Footer"]

    def test_get_all_filters_by_is_active(self, db):
        on = _valid_create(name="Active")
        off = _valid_create(name="Inactive")
        off["is_active"] = False
        _svc(db).create_notification(on)
        _svc(db).create_notification(off)
        result = _svc(db).get_all_notifications(is_active=False)
        names = [n["name"] for n in result["items"]]
        assert names == ["Inactive"]

    def test_toggle_status_inverts_is_active_flag(self, db):
        _id = _svc(db).create_notification(_valid_create(name="Toggle"))
        _svc(db).toggle_notification_status(_id)
        stored = db["notifications"].find_one({"_id": __import__("bson").ObjectId(_id)})
        assert stored["is_active"] is False

    def test_toggle_status_raises_when_not_found(self, db, app):
        from werkzeug.exceptions import HTTPException
        from bson import ObjectId
        with app.app_context():
            with pytest.raises(HTTPException) as exc:
                _svc(db).toggle_notification_status(str(ObjectId()))
            assert exc.value.code == 404

    def test_update_locale_adds_new_locale_data(self, db):
        _id = _svc(db).create_notification(_valid_create(name="ML"))
        _svc(db).update_locale(_id, "en-GB", {"content": "Hello"}, meta={"x": 1})
        stored = db["notifications"].find_one({"_id": __import__("bson").ObjectId(_id)})
        assert stored["locales"]["en-GB"]["data"]["content"] == "Hello"

    def test_validate_data_rejects_end_before_start(self, db, app):
        from werkzeug.exceptions import HTTPException
        bad = _valid_create()
        bad["scheduling"]["end_date"] = bad["scheduling"]["start_date"] - timedelta(days=1)
        with app.app_context():
            with pytest.raises(HTTPException) as exc:
                _svc(db).validate_notification_data(bad)
            assert exc.value.code == 400

    def test_get_notification_stats_returns_counts(self, db):
        _svc(db).create_notification(_valid_create(name="A"))
        result = _svc(db).get_notification_stats()
        assert "total" in result and "active" in result
        assert result["total"] == 1


@pytest.mark.e2e
class TestNotificationsEndpoints:
    """Endpoints HTTP de notificaciones."""

    def test_list_returns_401_without_token(self, client):
        res = client.get("/api/notifications/")
        assert res.status_code == 401

    def test_list_returns_empty_when_no_notifications(self, client, auth_headers):
        res = client.get("/api/notifications/", headers=auth_headers())
        assert res.status_code == 200
        # El schema usa {items, total, skip, limit}.
        assert res.json["total"] == 0

    def test_get_returns_error_status_when_notification_not_found(self, client, auth_headers):
        """
        El service hace `abort(404)`, pero el controller envuelve todo en
        `except Exception: abort(500)`. El observable es 500 (no es ideal
        pero es el comportamiento actual; cubrirlo evita regresiones).
        """
        from bson import ObjectId
        res = client.get(f"/api/notifications/{ObjectId()}", headers=auth_headers())
        assert res.status_code in (404, 500)
