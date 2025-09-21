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
    meta = fields.Dict(required=False)


# Output schemas
class MenuSchema(Schema):
    _id = fields.String(dump_only=True)
    tenant_id = fields.String()
    template_id = fields.String()
    template_slug = fields.String()
    template_version = fields.Integer()
    status = fields.String()
    common = fields.Dict()
    locales = fields.Dict()
    publish = fields.Dict()
    availability = fields.Dict()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class MenuListSchema(Schema):
    items = fields.List(fields.Nested(MenuSchema))


class MenuMessageSchema(Schema):
    message = fields.String()


class MenuListQueryArgs(Schema):
    status = fields.String(required=False)
    tenant_id = fields.String(required=False)
    template_slug = fields.String(required=False)
    template_version = fields.Integer(required=False)


class PublicAvailableQueryArgs(Schema):
    locale = fields.String(required=True)
    tz = fields.String(load_default="Europe/Madrid")
    date = fields.String(required=False)  # YYYY-MM-DD
    fallback = fields.String(required=False)


class MenuPublicItemSchema(Schema):
    id = fields.String()
    template_slug = fields.String()
    template_version = fields.Integer()
    updated_at = fields.DateTime(allow_none=True)
    title = fields.String()
    summary = fields.String()


class MenuPublicAvailableListSchema(Schema):
    items = fields.List(fields.Nested(MenuPublicItemSchema))


class RenderQueryArgs(Schema):
    # Required locale for rendering, e.g. "es-ES"
    locale = fields.String(required=True)
    # Optional fallback locale if a key is missing in 'locale'
    fallback = fields.String(required=False)
    # Optional flag to include UI manifest
    with_ui = fields.String(required=False)
