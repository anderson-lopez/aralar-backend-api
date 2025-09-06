from marshmallow import Schema, fields


class MenuCreateSchema(Schema):
    tenant_id = fields.String(required=True)
    template_id = fields.String(required=False)  # either this...
    template_slug = fields.String(required=False)  # ...or these two
    template_version = fields.Integer(required=False)
    status = fields.String(load_default="draft")
    common = fields.Dict(required=True)  # only non-translatable fields
    locales = fields.Dict(required=False)  # e.g., { "es-ES": {...}, "en-GB": {...} }


class MenuCommonUpdateSchema(Schema):
    common = fields.Dict(required=True)


class MenuLocaleUpdateSchema(Schema):
    data = fields.Dict(required=True)  # localized subtree for that locale
