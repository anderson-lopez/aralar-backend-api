from marshmallow import Schema, fields


class UploadPresignRequestSchema(Schema):
    filename = fields.String(required=True)
    mime = fields.String(required=True)
    folder = fields.String(load_default="menus")


class UploadPresignResponseSchema(Schema):
    upload_url = fields.String()
    public_url = fields.String()
    key = fields.String()


class UploadsMessageSchema(Schema):
    message = fields.String()


class UploadProxyFormSchema(Schema):
    # upload_url (presigned) passed as form field
    upload_url = fields.String(required=True)
    # file to upload (documented for Swagger as binary)
    file = fields.Raw(required=True, metadata={"type": "string", "format": "binary"})


class UploadDirectFormSchema(Schema):
    # optional target folder inside bucket (defaults to "menus")
    folder = fields.String(required=False)
    # optional explicit filename and mime; if omitted, use uploaded file name and mimetype
    filename = fields.String(required=False)
    mime = fields.String(required=False)
    file = fields.Raw(required=True, metadata={"type": "string", "format": "binary"})
