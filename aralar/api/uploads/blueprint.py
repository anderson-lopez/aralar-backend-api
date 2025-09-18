from flask_smorest import Blueprint, abort
from flask import request
import requests
import uuid
from botocore.exceptions import ClientError
from botocore.config import Config as BotoConfig
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
import boto3
import os
import tempfile

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
    try:
        return svc.presign(filename, mime)
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
    # Permitir que el frontend especifique el Content-Type exacto usado en el presign
    content_type = (request.form or {}).get("content_type")
    
    if not upload_url:
        abort(422, message="upload_url is required")
    if not file:
        abort(422, message="file is required")

    # Stream the file to the presigned URL. Content-Type y ACL DEBEN coincidir con los usados en presign
    headers = {}
    # Usar content_type del form si está disponible, sino usar el mimetype del archivo
    mime_to_use = content_type or getattr(file, "mimetype", None)
    if mime_to_use:
        headers["Content-Type"] = mime_to_use
    
    # 🔑 CLAVE: Agregar ACL header que coincida con el usado en presign
    headers["x-amz-acl"] = "public-read"
    
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
        # ✅ El archivo ya es público gracias al header x-amz-acl
        return {"message": "ok", "etag": etag}
    else:
        # Try to surface upstream error body if available
        detail = None
        try:
            detail = resp.text[:500]
        except Exception:
            detail = None
        abort(400, message=f"upstream status={resp.status_code} body={detail}")


@blp.route("/presign-info", methods=["GET"])
@blp.doc(
    description=(
        "Información sobre cómo usar URLs presignadas desde el frontend.\n\n"
        "**IMPORTANTE para Frontend:**\n"
        "1. Solicita presign: `POST /presign {filename, mime}`\n"
        "2. Recibe: `{upload_url, public_url, key}`\n"
        "3. Haz PUT a upload_url con estos headers OBLIGATORIOS:\n"
        "   - `Content-Type: [mismo mime del presign]`\n"
        "   - `x-amz-acl: public-read`\n"
        "4. El archivo quedará público automáticamente\n\n"
        "**Ejemplo JavaScript:**\n"
        "```javascript\n"
        "const response = await fetch(uploadUrl, {\n"
        "  method: 'PUT',\n"
        "  headers: {\n"
        "    'Content-Type': mimeType,\n"
        "    'x-amz-acl': 'public-read'\n"
        "  },\n"
        "  body: file\n"
        "});\n"
        "```"
    )
)
def presign_info():
    return {
        "message": "Presign URL usage information",
        "required_headers": {
            "Content-Type": "Must match the mime type used in presign request",
            "x-amz-acl": "Must be 'public-read' to make file publicly accessible"
        },
        "example": {
            "method": "PUT",
            "headers": {
                "Content-Type": "image/jpeg",
                "x-amz-acl": "public-read"
            }
        }
    }


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
    filename = (request.form or {}).get("filename") or getattr(file, "filename", "file.bin")
    mime = (request.form or {}).get("mime") or getattr(file, "mimetype", "application/octet-stream")

    try:
        content_length = getattr(file, "content_length", None)
        # If Flask didn't provide content_length, try to compute it via seek/tell
        if content_length is None:
            try:
                cur = file.stream.tell()
                file.stream.seek(0, 2)  # end
                end = file.stream.tell()
                file.stream.seek(cur, 0)
                content_length = end - cur
            except Exception:
                content_length = None

        fileobj = file.stream
        # As a last resort for providers that strictly require Content-Length and stream is not seekable,
        # we buffer into memory once (only if content_length is still unknown).
        if content_length is None:
            try:
                data = file.read()
                content_length = len(data)
                from io import BytesIO

                fileobj = BytesIO(data)
            except Exception:
                pass

        result = svc.upload_direct(
            fileobj=fileobj,
            filename=filename,
            mime=mime,
        )
        return result
    except ValueError as e:
        abort(400, message=str(e))


@blp.route("/bucket-exists-boto", methods=["GET"])
@require_permissions("menus:update")
@blp.doc(
    security=[{"bearerAuth": []}],
    description="Comprueba existencia del bucket usando boto3 (head_bucket)",
)
def bucket_exists_boto():
    bucket = svc.storage.bucket
    try:
        head = svc.storage.client.head_bucket(Bucket="aralar-media")
        # Convert 'head' object to string to ensure it's JSON serializable
        return {"message": "exists", "bucket": bucket, "head": str(head)}
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code") if hasattr(e, "response") else None
        # 404 Not Found => bucket no existe
        if code in ("404", "NoSuchBucket"):
            return {"message": "missing", "bucket": bucket}
        abort(400, message=f"boto3 error: {e}")
    except Exception as e:
        abort(400, message=f"boto3 error: {e}")
