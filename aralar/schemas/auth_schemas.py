import re
from marshmallow import Schema, fields, validate, ValidationError, validates_schema


def validate_password_strength(password):
    """Valida que la contraseña tenga al menos una mayúscula, una minúscula y un número"""
    has_upper = re.search(r"[A-Z]", password)
    has_lower = re.search(r"[a-z]", password)
    has_digit = re.search(r"\d", password)

    if not (has_upper and has_lower and has_digit):
        raise ValidationError(
            "Password must contain at least one uppercase letter, one lowercase letter, and one number"
        )


def validate_email_format(email):
    """Valida el formato del email usando regex"""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.search(email_pattern, email):
        raise ValidationError("Invalid email format")


def validate_full_name(name):
    """Valida el nombre completo"""
    if not name or not name.strip():
        raise ValidationError("Full name is required")
    if len(name) > 50:
        raise ValidationError("Full name must be 50 characters or less")
    # Validar que solo contenga letras, espacios y algunos caracteres especiales
    if not re.search(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\'-]+$", name):
        raise ValidationError("Full name can only contain letters, spaces, hyphens and apostrophes")


class LoginSchema(Schema):
    email = fields.String(
        required=True,
        validate=[
            validate_email_format,
            validate.Length(min=5, max=100, error="Email must be between 5 and 100 characters"),
        ],
        metadata={"example": "admin@aralar.local", "description": "User email address"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters"),
        metadata={"example": "ChangeMeNow!2025", "description": "User password"},
    )

    class Meta:
        # Ejemplo completo del body para Swagger
        example = {"email": "admin@example.com", "password": "admin123"}


class RegisterSchema(Schema):
    email = fields.String(
        required=True,
        validate=[
            validate_email_format,
            validate.Length(min=5, max=100, error="Email must be between 5 and 100 characters"),
        ],
        metadata={"example": "user@example.com", "description": "User email address"},
    )
    password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters"),
            validate_password_strength,
        ],
        metadata={"example": "SecurePass123!", "description": "User password (min 8 characters)"},
    )
    confirm_password = fields.String(
        required=True,
        metadata={"example": "SecurePass123!", "description": "Password confirmation"},
    )
    full_name = fields.String(
        required=True,
        validate=validate_full_name,
        metadata={"example": "John Doe", "description": "User full name"},
    )

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Valida que las contraseñas coincidan"""
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match", field_name="confirm_password")

    class Meta:
        example = {
            "email": "user@example.com",
            "password": "SecurePass123!",
            "confirm_password": "SecurePass123!",
            "full_name": "John Doe",
        }


class ChangePasswordSchema(Schema):
    old_password = fields.String(
        required=True,
        validate=validate.Length(
            min=8, max=128, error="Old password must be between 8 and 128 characters"
        ),
        metadata={"example": "OldPassword321?", "description": "User old password"},
    )
    new_password = fields.String(
        required=True,
        validate=[
            validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters"),
            validate_password_strength,
        ],
        metadata={"example": "NewPassword321?", "description": "User new password"},
    )
    confirm_new_password = fields.String(
        required=True,
        validate=validate.Length(
            min=8, max=128, error="Password confirmation must be between 8 and 128 characters"
        ),
        metadata={"example": "NewPassword321?", "description": "User confirm new password"},
    )

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Valida que las nuevas contraseñas coincidan"""
        new_password = data.get("new_password")
        confirm_new_password = data.get("confirm_new_password")

        if new_password and confirm_new_password and new_password != confirm_new_password:
            raise ValidationError("New passwords do not match", field_name="confirm_new_password")


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
