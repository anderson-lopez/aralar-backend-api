from marshmallow import Schema, fields


class MenuCreateSchema(Schema):
    tenant_id = fields.String(required=True)
    template_id = fields.String(required=False)  # either this...
    template_slug = fields.String(required=False)  # ...or these two
    template_version = fields.Integer(required=False)
    status = fields.String(load_default="draft")
    common = fields.Dict(required=True)  # only non-translatable fields
    locales = fields.Dict(required=False)  # e.g., { "es-ES": {...}, "en-GB": {...} }
    featured = fields.Boolean(load_default=False)  # if menu is featured for landing
    featured_order = fields.Integer(required=False)  # order priority (lower = higher priority)


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
    featured = fields.Boolean()
    featured_order = fields.Integer(allow_none=True)
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


class PublicFeaturedQueryArgs(Schema):
    """Schema for featured menus query parameters"""
    locale = fields.String(required=True)
    tz = fields.String(load_default="Europe/Madrid")
    date = fields.String(required=False)  # YYYY-MM-DD
    fallback = fields.String(required=False)
    include_ui = fields.Boolean(load_default=False)  # Include UI manifest


class MenuPublicItemSchema(Schema):
    id = fields.String()
    template_slug = fields.String()
    template_version = fields.Integer()
    updated_at = fields.DateTime(allow_none=True)
    title = fields.String()
    summary = fields.String()


class MenuPublicAvailableListSchema(Schema):
    items = fields.List(fields.Nested(MenuPublicItemSchema))


class MenuFeaturedUpdateSchema(Schema):
    """Schema for updating featured status and order of a menu"""
    featured = fields.Boolean(required=True)
    featured_order = fields.Integer(required=False, allow_none=True)


class MenuFeaturedItemSchema(Schema):
    """Schema for featured menu items returned to frontend"""
    id = fields.String()
    template_slug = fields.String()
    template_version = fields.Integer()
    title = fields.String()
    summary = fields.String()
    featured_order = fields.Integer(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    # Full rendered menu data ready for display
    data = fields.Dict()
    meta = fields.Dict()
    ui = fields.Dict(required=False)  # Optional UI manifest


class MenuFeaturedListSchema(Schema):
    """Schema for list of featured menus"""
    items = fields.List(fields.Nested(MenuFeaturedItemSchema))


class RenderQueryArgs(Schema):
    # Required locale for rendering, e.g. "es-ES"
    locale = fields.String(required=True)
    # Optional fallback locale if a key is missing in 'locale'
    fallback = fields.String(required=False)
    # Optional flag to include UI manifest
    include_ui = fields.Boolean(load_default=False)


class RenderMultipleSchema(Schema):
    """Schema for rendering multiple menus at once"""
    menu_ids = fields.List(fields.String(), required=True, validate=lambda x: len(x) <= 10)  # Max 10 menus
    locale = fields.String(required=True)
    fallback = fields.String(required=False)
    include_ui = fields.Boolean(load_default=False)


class RenderedMenuSchema(Schema):
    """Schema for a single rendered menu"""
    id = fields.String()
    tenant_id = fields.String()
    template = fields.Dict()
    locale = fields.String()
    fallback_used = fields.String(allow_none=True)
    data = fields.Dict()
    meta = fields.Dict()
    published_at = fields.String(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    ui = fields.Dict(required=False)  # Optional UI manifest


class RenderMultipleResponseSchema(Schema):
    """Schema for multiple rendered menus response"""
    items = fields.List(fields.Nested(RenderedMenuSchema))
    errors = fields.Dict(required=False)  # Map of menu_id -> error_message for failed renders
