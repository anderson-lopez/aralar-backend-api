from flask_smorest import Blueprint, abort
from flask import request
import requests
from botocore.exceptions import ClientError
from ...services.uploads_service import UploadsService
from urllib.parse import urlparse
from minio import Minio
from ...core.security import require_permissions
from ...schemas.uploads_schemas import (
    UploadPresignRequestSchema,
    UploadPresignResponseSchema,
    UploadsMessageSchema,
    UploadProxyFormSchema,
    UploadDirectFormSchema,
)

blp = Blueprint("uploads", "uploads", description="Uploads (presigned)")

svc = UploadsService()


@blp.route("/presign", methods=["POST"])
@require_permissions("menus:update")
@blp.arguments(UploadPresignRequestSchema)
@blp.response(200, UploadPresignResponseSchema)
@blp.alt_response(400, schema=UploadsMessageSchema)
@blp.alt_response(422, schema=UploadsMessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def presign(body):
    filename = body.get("filename")
    mime = body.get("mime")
    folder = body.get("folder", "menus")
    try:
        return svc.presign(filename, mime, folder)
    except ValueError as e:
        abort(400, message=str(e))


@blp.route("/proxy-put", methods=["POST"])
@require_permissions("menus:update")
@blp.response(200, UploadsMessageSchema)
@blp.alt_response(400, schema=UploadsMessageSchema)
@blp.alt_response(422, schema=UploadsMessageSchema, description="Validation error")
@blp.doc(
    security=[{"bearerAuth": []}],
    description=(
        "Proxy para simular la subida desde frontend: envía un archivo (multipart/form-data)\n"
        "y una URL presignada (upload_url). El backend hará un PUT binario a esa URL."
    ),
    requestBody={
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": UploadProxyFormSchema,
            }
        },
    },
)
def proxy_put_upload():
    upload_url = (request.form or {}).get("upload_url")
    file = (request.files or {}).get("file")
    if not upload_url:
        abort(422, message="upload_url is required")
    if not file:
        abort(422, message="file is required")

    # Stream the file to the presigned URL. Some providers require Content-Type to match the one used to generate the URL.
    headers = {}
    if getattr(file, "mimetype", None):
        headers["Content-Type"] = file.mimetype
    # Some servers behave better with an explicit Content-Length
    content_length = getattr(file, "content_length", None)
    if isinstance(content_length, int) and content_length >= 0:
        headers["Content-Length"] = str(content_length)
    try:
        print("[s3] proxy_put_upload")
        print("[s3] upload_url: ", upload_url)
        resp = requests.put(
            upload_url,
            data=file.stream,  # stream directly to avoid buffering and mismatched lengths
            headers=headers,
            timeout=300,
        )
    except requests.RequestException as e:
        abort(400, message=f"upload failed: {e}")

    if 200 <= resp.status_code < 300:
        etag = resp.headers.get("ETag")
        return {"message": "ok", "etag": etag}
    else:
        # Try to surface upstream error body if available
        detail = None
        try:
            detail = resp.text[:500]
        except Exception:
            detail = None
        abort(400, message=f"upstream status={resp.status_code} body={detail}")


@blp.route("/direct", methods=["POST"])
@require_permissions("menus:update")
@blp.response(200, UploadPresignResponseSchema)
@blp.alt_response(400, schema=UploadsMessageSchema)
@blp.alt_response(422, schema=UploadsMessageSchema, description="Validation error")
@blp.doc(
    security=[{"bearerAuth": []}],
    description=(
        "Sube el archivo directamente al bucket desde el backend (sin presigned).\n"
        "Envia multipart/form-data con el campo 'file' y opcionalmente 'folder', 'filename', 'mime'."
    ),
    requestBody={
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": UploadDirectFormSchema,
            }
        },
    },
)
def upload_direct():
    file = (request.files or {}).get("file")
    if not file:
        abort(422, message="file is required")
    folder = (request.form or {}).get("folder") or "menus"
    filename = (request.form or {}).get("filename") or getattr(file, "filename", "file.bin")
    mime = (request.form or {}).get("mime") or getattr(file, "mimetype", "application/octet-stream")

    try:
        result = svc.upload_direct(fileobj=file.stream, filename=filename, mime=mime, folder=folder)
        return result
    except ValueError as e:
        abort(400, message=str(e))


@blp.route("/health", methods=["GET"])
@require_permissions("menus:update")
@blp.response(200, UploadsMessageSchema)
@blp.doc(
    security=[{"bearerAuth": []}],
    description="Diagnóstico de conectividad con MinIO/S3 desde el backend",
)
def uploads_health():
    # 1) Ping HTTP de salud de MinIO (si es MinIO)
    import os

    endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000").rstrip("/")
    health_url = f"{endpoint}/minio/health/live"
    http_ok = None
    http_status = None
    try:
        r = requests.get(health_url, timeout=5)
        http_ok = r.ok
        http_status = r.status_code
    except Exception as e:
        http_ok = False
        http_status = str(e)

    # 2) HEAD bucket con boto3 (credenciales/ACL)
    bucket_ok = None
    bucket_error = None
    try:
        svc.storage.client.head_bucket(Bucket=svc.storage.bucket)
        bucket_ok = True
    except Exception as e:
        bucket_ok = False
        bucket_error = str(e)

    return {
        "message": "ok" if http_ok and bucket_ok else "error",
        "endpoint": endpoint,
        "health_http_ok": http_ok,
        "health_http_status": http_status,
        "bucket": svc.storage.bucket,
        "head_bucket_ok": bucket_ok,
        "head_bucket_error": bucket_error,
    }


@blp.route("/bucket-exists", methods=["GET"])
@require_permissions("menus:update")
@blp.response(200, UploadsMessageSchema)
@blp.doc(
    security=[{"bearerAuth": []}], description="Comprueba existencia del bucket usando MinIO SDK"
)
def bucket_exists_check():
    import os

    endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    access_key = os.getenv("S3_ACCESS_KEY", "minio")
    secret_key = os.getenv("S3_SECRET_KEY", "minio123")
    bucket = os.getenv("S3_BUCKET", "aralar-media")

    # Parse endpoint for Minio(host:port, secure)
    secure = False
    hostport = endpoint
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        u = urlparse(endpoint)
        secure = u.scheme == "https"
        hostport = f"{u.hostname}:{u.port or (443 if secure else 80)}"

    try:
        mc = Minio(hostport, access_key=access_key, secret_key=secret_key, secure=secure)
        exists = mc.bucket_exists(bucket)
        return {
            "message": "exists" if exists else "missing",
            "bucket": bucket,
            "endpoint": endpoint,
        }
    except Exception as e:
        abort(400, message=f"minio error: {e}")


@blp.route("/bucket-exists-boto", methods=["GET"])
@require_permissions("menus:update")
@blp.response(200, UploadsMessageSchema)
@blp.doc(
    security=[{"bearerAuth": []}],
    description="Comprueba existencia del bucket usando boto3 (head_bucket)",
)
def bucket_exists_boto():
    bucket = svc.storage.bucket
    try:
        svc.storage.client.head_bucket(Bucket=bucket)
        return {"message": "exists", "bucket": bucket}
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        # 404 Not Found => bucket no existe
        if code in ("404", "NoSuchBucket"):
            return {"message": "missing", "bucket": bucket}
        abort(400, message=f"boto3 error: {e}")
    except Exception as e:
        abort(400, message=f"boto3 error: {e}")
