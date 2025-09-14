from flask_smorest import Blueprint, abort
from flask import request
from ...services.uploads_service import UploadsService
from ...core.security import require_permissions
from ...schemas.uploads_schemas import (
    UploadPresignRequestSchema,
    UploadPresignResponseSchema,
    MessageSchema,
)

blp = Blueprint("uploads", "uploads", description="Uploads (presigned)")

svc = UploadsService()


@blp.route("/presign", methods=["POST"])
@require_permissions("menus:update")
@blp.arguments(UploadPresignRequestSchema)
@blp.response(200, UploadPresignResponseSchema)
@blp.alt_response(400, schema=MessageSchema)
@blp.alt_response(422, schema=MessageSchema, description="Validation error")
@blp.doc(security=[{"bearerAuth": []}])
def presign(body):
    filename = body.get("filename")
    mime = body.get("mime")
    folder = body.get("folder", "menus")
    try:
        return svc.presign(filename, mime, folder)
    except ValueError as e:
        abort(400, message=str(e))
