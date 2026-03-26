from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from .auth_schemas import validate_password_strength


# ObjectIdField no se usa actualmente, usando fields.Method() en su lugar


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        validate=[
            validate.Length(
                min=8, max=128, error="Password must be between 8 and 128 characters"
            ),
            validate_password_strength,
        ],
    )
    confirm_password = fields.String(required=True)
    full_name = fields.String(
        required=True,
        validate=validate.Length(
            min=1, max=50, error="Full name must be between 1 and 50 characters"
        ),
    )
    roles = fields.List(fields.String(), load_default=[])
    permissions_allow = fields.List(fields.String(), load_default=[])
    permissions_deny = fields.List(fields.String(), load_default=[])

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match", field_name="confirm_password")


class UserOutSchema(Schema):
    id = fields.String(attribute="_id")
    email = fields.Email()
    full_name = fields.String()
    roles = fields.List(fields.String())
    permissions_allow = fields.List(fields.String())
    permissions_deny = fields.List(fields.String())
    is_active = fields.Boolean()
    created_at = fields.String()
    updated_at = fields.String()


class UserUpdateSchema(Schema):
    email = fields.Email(required=False)
    full_name = fields.String(
        required=False,
        validate=validate.Length(
            min=1, max=50, error="Full name must be between 1 and 50 characters"
        ),
    )
    roles = fields.List(fields.String(), required=False)
    permissions_allow = fields.List(fields.String(), required=False)
    permissions_deny = fields.List(fields.String(), required=False)


class UserPermsUpdateSchema(Schema):
    permissions_allow = fields.List(fields.String(), load_default=[])
    permissions_deny = fields.List(fields.String(), load_default=[])


class UserRolesUpdateSchema(Schema):
    roles = fields.List(fields.String(), required=True)


class UserListResponseSchema(Schema):
    items = fields.List(fields.Nested(UserOutSchema))
    total = fields.Integer()
    skip = fields.Integer()
    limit = fields.Integer()


class UserCreateResponseSchema(Schema):
    id = fields.String()


class UserDeleteResponseSchema(Schema):
    message = fields.String()


class UserListQueryArgs(Schema):
    skip = fields.Integer(load_default=0)
    limit = fields.Integer(load_default=20)
