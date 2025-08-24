from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        metadata={"example": "admin@aralar.local", "description": "User email address"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=1),
        metadata={"example": "ChangeMeNow!2025", "description": "User password"},
    )

    class Meta:
        # Ejemplo completo del body para Swagger
        example = {"email": "admin@example.com", "password": "admin123"}


class LoginResponseSchema(Schema):
    access_token = fields.String()
    refresh_token = fields.String()


class AuthErrorSchema(Schema):
    message = fields.String()
    error = fields.String(load_default=None)
    errors = fields.Dict(load_default={})


class UserInfoSchema(Schema):
    user_id = fields.String()
    email = fields.Email()
    roles = fields.List(fields.String())
    permissions = fields.List(fields.String())
