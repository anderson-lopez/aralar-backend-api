from marshmallow import Schema, fields, validate, ValidationError

DOW = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


# Field definitions for template
class FieldSchema(Schema):
    key = fields.String(required=True)
    type = fields.String(
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
    label = fields.Dict(keys=fields.String(), values=fields.String(), required=False)  # i18n labels
    required = fields.Boolean(load_default=False)
    translatable = fields.Boolean(load_default=False)
    maxLength = fields.Integer(required=False)
    min = fields.Float(required=False)
    max = fields.Float(required=False)
    enum = fields.List(fields.String(), required=False)
    currency = fields.String(required=False)
    itemSchema = fields.Nested(lambda: ItemSchema(), required=False)  # for type=list


class ItemSchema(Schema):
    fields = fields.List(fields.Nested(FieldSchema), required=True)


class SectionSchema(Schema):
    key = fields.String(required=True)
    label = fields.Dict(keys=fields.String(), values=fields.String())
    repeatable = fields.Boolean(required=True)
    minItems = fields.Integer(required=False)
    maxItems = fields.Integer(required=False)
    fields = fields.List(fields.Nested(FieldSchema), required=True)


class MenuTemplateCreateSchema(Schema):
    name = fields.String(required=True)
    slug = fields.String(required=True)
    version = fields.Integer(load_default=1)
    status = fields.String(
        load_default="draft", validate=validate.OneOf(["draft", "published", "archived"])
    )
    tenant_id = fields.String(required=True)
    i18n = fields.Dict(required=False)
    sections = fields.List(fields.Nested(SectionSchema), required=True)
    ui = fields.Dict(required=False)


class MenuTemplateUpdateSchema(MenuTemplateCreateSchema):
    # same fields; at service enforce status draft-only for updates
    pass


class MenuTemplatePublishSchema(Schema):
    # opcionalmente forzar nuevo slug/notes; aquí solo placeholder
    notes = fields.String(required=False)


# Respuesta completa de un template (incluye metadatos comunes)
class MenuTemplateSchema(Schema):
    _id = fields.String(dump_only=True)
    name = fields.String(required=True)
    slug = fields.String(required=True)
    version = fields.Integer()
    status = fields.String(validate=validate.OneOf(["draft", "published", "archived"]))
    tenant_id = fields.String(required=True)
    i18n = fields.Dict()
    sections = fields.List(fields.Nested(SectionSchema))
    ui = fields.Dict()
    publish_notes = fields.String(load_default="", dump_default="")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class MenuTemplateListSchema(Schema):
    items = fields.List(fields.Nested(MenuTemplateSchema))


class IdSchema(Schema):
    id = fields.String()


class MessageSchema(Schema):
    message = fields.String()


class MenuTemplateQueryArgs(Schema):
    status = fields.String(required=False, validate=validate.OneOf(["draft", "published", "archived"]))
    slug = fields.String(required=False)
    tenant_id = fields.String(required=False)
