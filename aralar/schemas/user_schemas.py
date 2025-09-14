from marshmallow import Schema, fields, validate


# ObjectIdField no se usa actualmente, usando fields.Method() en su lugar


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(
        required=True, 
        validate=validate.Length(min=8, max=128, error="Password must be between 8 and 128 characters")
    )
    confirm_password = fields.String(required=True)
    full_name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=50, error="Full name must be between 1 and 50 characters")
    )
    roles = fields.List(fields.String(), load_default=[])
    permissions_allow = fields.List(fields.String(), load_default=[])
    permissions_deny = fields.List(fields.String(), load_default=[])


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


class UserPermsUpdateSchema(Schema):
    permissions_allow = fields.List(fields.String(), load_default=[])
    permissions_deny = fields.List(fields.String(), load_default=[])


class UserRolesUpdateSchema(Schema):
    roles = fields.List(fields.String(), required=True)


class UserListResponseSchema(Schema):
    items = fields.List(fields.Nested(UserOutSchema))


class UserCreateResponseSchema(Schema):
    id = fields.String()
