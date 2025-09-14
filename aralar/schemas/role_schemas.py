from marshmallow import Schema, fields


class RoleSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(load_default="", dump_default="")
    permissions = fields.List(fields.String(), load_default=list, dump_default=list)


class RoleCreateUpdateSchema(Schema):
    # For POST /roles we will require name; for PUT it's passed in path
    name = fields.String(required=False)
    description = fields.String(load_default="")
    permissions = fields.List(fields.String(), load_default=list)


class RoleListSchema(Schema):
    items = fields.List(fields.Nested(RoleSchema))


class PermissionSchema(Schema):
    name = fields.String(required=True)
    description = fields.String(load_default="", dump_default="")


class PermissionUpsertSchema(Schema):
    description = fields.String(load_default="")


class PermissionListSchema(Schema):
    items = fields.List(fields.Nested(PermissionSchema))


class RoleMessageSchema(Schema):
    message = fields.String()
