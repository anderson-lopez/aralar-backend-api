"""
Tests del módulo de uploads (presign URLs de S3/MinIO).

Referencias:
- Blueprint: `aralar/api/uploads/blueprint.py`
- Service:   `aralar/services/uploads_service.py`

⚠️ ATENCIÓN: este módulo llama a S3/MinIO. Hay que MOCKEAR el cliente boto3
para que los tests no intenten conectarse a un storage real.

Ejemplo de mock:
    from unittest.mock import patch, MagicMock

    @patch("aralar.services.uploads_service.boto3.client")
    def test_presign_returns_upload_url(mock_boto, client, auth_headers):
        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://fake-upload.url"
        mock_boto.return_value = mock_s3

        res = client.post("/api/uploads/presign", json={...}, headers=auth_headers())
        assert res.status_code == 200
"""
import pytest


@pytest.mark.e2e
class TestPresignUpload:
    """
    POST /api/uploads/presign

    TODO (junior):
    - test_returns_401_without_token
    - test_returns_upload_url_and_public_url
    - test_returns_400_when_mime_not_allowed
    - test_returns_400_when_filename_missing
    - test_calls_boto_with_correct_bucket_and_key
    """
    pass
