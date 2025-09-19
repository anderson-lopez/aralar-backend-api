from marshmallow import Schema, fields as ma_fields, validate, ValidationError

DOW = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


class UIHintsSchema(Schema):
    choose_count = ma_fields.Integer(required=False)
    scope = ma_fields.String(required=False, validate=validate.OneOf(["per_table", "per_person"]))
    show_price = ma_fields.Boolean(required=False)
    icon = ma_fields.String(required=False)


class SectionUISchema(Schema):
    role = ma_fields.String(
        required=True,
        validate=validate.OneOf(
            ["header", "course_list", "extras", "legend", "note", "price_footer"]
        ),
    )
    order = ma_fields.Integer(required=True)
    display = ma_fields.String(
        required=True,
        validate=validate.OneOf(
            ["hero", "list", "bullets", "table", "grid", "legend", "footer_price"]
        ),
    )
    hints = ma_fields.Nested(UIHintsSchema, required=False)


# Field definitions for template
class FieldSchema(Schema):
    key = ma_fields.String(required=True)
    type = ma_fields.String(
        required=True,
        validate=validate.OneOf(
            [
                "text",
                "textarea",
                "rich_text",
                "number",
                "price",
                "boolean",
                "date",
                "time",
                "datetime",
                "enum",
                "multi_enum",
                "tags",
                "image",
                "list",
                "group",
                "reference",
                "divider",
                "subtitle",
            ]
        ),
    )
    label = ma_fields.Dict(keys=ma_fields.String(), values=ma_fields.String(), required=False)  # i18n labels
    required = ma_fields.Boolean(load_default=False)
    translatable = ma_fields.Boolean(load_default=False)
    maxLength = ma_fields.Integer(required=False)
    min = ma_fields.Float(required=False)
    max = ma_fields.Float(required=False)
    enum = ma_fields.List(ma_fields.String(), required=False)
    currency = ma_fields.String(required=False)
    itemSchema = ma_fields.Nested(lambda: ItemSchema(), required=False)  # for type=list


class ItemSchema(Schema):
    fields = ma_fields.List(ma_fields.Nested(FieldSchema), required=True)


class SectionSchema(Schema):
    key = ma_fields.String(required=True)
    label = ma_fields.Dict(keys=ma_fields.String(), values=ma_fields.String())
    repeatable = ma_fields.Boolean(required=True)
    minItems = ma_fields.Integer(required=False)
    maxItems = ma_fields.Integer(required=False)
    fields = ma_fields.List(ma_fields.Nested(FieldSchema), required=True)
    ui = ma_fields.Nested(SectionUISchema, required=False)


class TemplateUICatalogAllergenSchema(Schema):
    code = ma_fields.String(required=True)
    icon = ma_fields.String(required=False)  # tu font/asset key


class TemplateUISchema(Schema):
    layout = ma_fields.String(required=False)  # "sections" por ahora
    catalogs = ma_fields.Dict(required=False)  # {"allergens":[...], "currency": {...}}


class MenuTemplateCreateSchema(Schema):
    name = ma_fields.String(required=True)
    slug = ma_fields.String(required=True)
    version = ma_fields.Integer(load_default=1)
    status = ma_fields.String(
        load_default="draft", validate=validate.OneOf(["draft", "published", "archived"])
    )
    tenant_id = ma_fields.String(required=True)
    i18n = ma_fields.Dict(required=False)
    sections = ma_fields.List(ma_fields.Nested(SectionSchema), required=True)
    ui = ma_fields.Nested(TemplateUISchema, required=False)  # <<--- NUEVO


class MenuTemplateUpdateSchema(MenuTemplateCreateSchema):
    # same fields; at service enforce status draft-only for updates
    pass


class MenuTemplatePublishSchema(Schema):
    # opcionalmente forzar nuevo slug/notes; aquí solo placeholder
    notes = ma_fields.String(required=False)


# Respuesta completa de un template (incluye metadatos comunes)
class MenuTemplateSchema(Schema):
    _id = ma_fields.String(dump_only=True)
    name = ma_fields.String(required=True)
    slug = ma_fields.String(required=True)
    version = ma_fields.Integer()
    status = ma_fields.String(validate=validate.OneOf(["draft", "published", "archived"]))
    tenant_id = ma_fields.String(required=True)
    i18n = ma_fields.Dict()
    sections = ma_fields.List(ma_fields.Nested(SectionSchema))
    ui = ma_fields.Dict()
    publish_notes = ma_fields.String(load_default="", dump_default="")
    created_at = ma_fields.DateTime(dump_only=True)
    updated_at = ma_fields.DateTime(dump_only=True)


class MenuTemplateListSchema(Schema):
    items = ma_fields.List(ma_fields.Nested(MenuTemplateSchema))


class IdSchema(Schema):
    id = ma_fields.String()


class MenuTemplateMessageSchema(Schema):
    message = ma_fields.String()


class MenuTemplateQueryArgs(Schema):
    status = ma_fields.String(
        required=False, validate=validate.OneOf(["draft", "published", "archived"])
    )
    slug = ma_fields.String(required=False)
    tenant_id = ma_fields.String(required=False)
