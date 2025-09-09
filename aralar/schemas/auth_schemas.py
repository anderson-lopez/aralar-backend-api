from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        metadata={"example": "admin@aralar.local", "description": "User email address"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8),
        metadata={"example": "ChangeMeNow!2025", "description": "User password"},
    )
    confirm_password = fields.String(
        required=True,
        metadata={"example": "ChangeMeNow!2025", "description": "Password confirmation"},
    )
    class Meta:
        # Ejemplo completo del body para Swagger
        example = {"email": "admin@example.com", "password": "admin123"}


class RegisterSchema(Schema):
    email = fields.Email(
        required=True,
        metadata={"example": "user@example.com", "description": "User email address"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8),
        metadata={"example": "SecurePass123!", "description": "User password (min 8 characters)"},
    )
    confirm_password = fields.String(
        required=True,
        metadata={"example": "SecurePass123!", "description": "Password confirmation"},
    )
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50),
        metadata={"example": "John Doe", "description": "User full name"},
    )

    class Meta:
        example = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "full_name": "John Doe"
        }

class ChangePasswordSchema(Schema):
    old_password = fields.String(
        required = True,
        validate = validate.Length(min=8),
        metadata = {"example": "OldPassword321?", "description": "User old password"}
    )
    new_password = fields.String(
        required = True,
        validate = validate.Length(min=8),
        metadata = {"example": "NewPassword321?", "description": "User new password"}
    )
    confirm_new_password = fields.String(
        required = True,
        validate = validate.Length(min=8),
        metadata = {"example": "NewPassword321?", "description": "User confirm new password"}
    )


class LoginResponseSchema(Schema):
    access_token = fields.String()
    refresh_token = fields.String()


class RegisterResponseSchema(Schema):
    message = fields.String(metadata={"example": "User registered successfully"})
    user_id = fields.String(metadata={"example": "507f1f77bcf86cd799439011"})

class ChangePasswordResponseSchema(Schema):
    message = fields.String(metadata={"example": "Password changed successfully"})

class AuthErrorSchema(Schema):
    message = fields.String()
    error = fields.String(load_default=None)
    errors = fields.Dict(load_default={})


class UserInfoSchema(Schema):
    user_id = fields.String()
    email = fields.Email()
    roles = fields.List(fields.String())
    permissions = fields.List(fields.String())
