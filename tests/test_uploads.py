"""
Tests del módulo de uploads (presign URLs de S3/MinIO).

Referencias:
- Blueprint: `aralar/api/uploads/blueprint.py`
- Service:   `aralar/services/uploads_service.py`

⚠️ Este módulo llama a S3/MinIO. Mockeamos el storage para que los tests no
intenten conectarse a un backend real. El svc del blueprint se instancia a
nivel módulo, así que parchamos su atributo `storage`.
"""
from unittest.mock import patch, MagicMock

import pytest


@pytest.mark.e2e
class TestPresignUpload:
    """POST /api/uploads/presign"""

    def test_returns_401_without_token(self, client):
        res = client.post("/api/uploads/presign", json={
            "filename": "foo.jpg", "mime": "image/jpeg",
        })
        assert res.status_code == 401

    def test_returns_403_when_user_lacks_menus_update_permission(self, client, auth_headers):
        res = client.post(
            "/api/uploads/presign",
            json={"filename": "foo.jpg", "mime": "image/jpeg"},
            headers=auth_headers(permissions=["menus:read"]),
        )
        assert res.status_code == 403

    def test_returns_upload_url_and_public_url_on_success(self, client, auth_headers):
        """Mockeamos el storage.presign_put para devolver URLs fake."""
        fake = MagicMock()
        fake.upload_url = "https://fake-upload-url"
        fake.public_url = "https://fake-public-url"
        fake.key = "menus/abc.jpg"

        with patch("aralar.api.uploads.blueprint.svc") as mock_svc:
            mock_svc.presign.return_value = {
                "upload_url": fake.upload_url,
                "public_url": fake.public_url,
                "key": fake.key,
            }
            res = client.post(
                "/api/uploads/presign",
                json={"filename": "foo.jpg", "mime": "image/jpeg"},
                headers=auth_headers(),
            )
        assert res.status_code == 200
        assert res.json["upload_url"] == "https://fake-upload-url"
        assert res.json["public_url"] == "https://fake-public-url"
        assert res.json["key"] == "menus/abc.jpg"

    def test_returns_400_when_mime_not_allowed(self, client, auth_headers):
        """Si el service levanta ValueError, el blueprint devuelve 400."""
        with patch("aralar.api.uploads.blueprint.svc") as mock_svc:
            mock_svc.presign.side_effect = ValueError("mime not allowed (text/plain)")
            res = client.post(
                "/api/uploads/presign",
                json={"filename": "doc.txt", "mime": "text/plain"},
                headers=auth_headers(),
            )
        assert res.status_code == 400

    def test_returns_422_when_filename_missing(self, client, auth_headers):
        res = client.post(
            "/api/uploads/presign",
            json={"mime": "image/jpeg"},  # filename ausente
            headers=auth_headers(),
        )
        assert res.status_code == 422

    def test_returns_422_when_mime_missing(self, client, auth_headers):
        res = client.post(
            "/api/uploads/presign",
            json={"filename": "foo.jpg"},  # mime ausente
            headers=auth_headers(),
        )
        assert res.status_code == 422


@pytest.mark.unit
class TestUploadsServiceValidation:
    """Tests unitarios de la validación interna del service."""

    def test_rejects_mime_outside_whitelist(self):
        from aralar.services.uploads_service import UploadsService
        svc = UploadsService()
        ok, err = svc._validate("foo.txt", "text/plain")
        assert ok is False
        assert "mime" in err.lower()

    def test_accepts_whitelisted_mime(self):
        from aralar.services.uploads_service import UploadsService
        svc = UploadsService()
        # image/jpeg está en la whitelist por defecto.
        ok, err = svc._validate("foo.jpg", "image/jpeg")
        assert ok is True
        assert err == ""
