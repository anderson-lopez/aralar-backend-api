from marshmallow import Schema, fields


class UploadPresignRequestSchema(Schema):
    filename = fields.String(required=True)
    mime = fields.String(required=True)
    folder = fields.String(load_default="menus")


class UploadPresignResponseSchema(Schema):
    upload_url = fields.String()
    public_url = fields.String()
    key = fields.String()


class MessageSchema(Schema):
    message = fields.String()

