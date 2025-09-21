from marshmallow import Schema, fields


class UploadPresignRequestSchema(Schema):
    filename = fields.String(required=True)
    mime = fields.String(required=True)


class UploadPresignResponseSchema(Schema):
    upload_url = fields.String()
    public_url = fields.String()
    key = fields.String()


class UploadsMessageSchema(Schema):
    message = fields.String()


class UploadProxyFormSchema(Schema):
    # upload_url (presigned) passed as form field
    upload_url = fields.String(required=True)
    # optional content_type to match the one used in presign (if different from file mimetype)
    content_type = fields.String(required=False)
    # file to upload (documented for Swagger as binary)
    file = fields.Raw(required=True, metadata={"type": "string", "format": "binary"})


class UploadDirectFormSchema(Schema):
    # optional explicit filename and mime; if omitted, use uploaded file name and mimetype
    filename = fields.String(required=False)
    mime = fields.String(required=False)
    file = fields.Raw(required=True, metadata={"type": "string", "format": "binary"})
