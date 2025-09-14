from marshmallow import Schema, fields


class TranslateItemSchema(Schema):
    source = fields.String()
    translated = fields.String()
    cached = fields.Boolean()


class TranslateRequestSchema(Schema):
    texts = fields.List(fields.String(), required=True)
    source_lang = fields.String(required=False)
    target_lang = fields.String(required=True)
    tenant_id = fields.String(required=True)
    use_glossary = fields.Boolean(load_default=True)


class TranslateResponseSchema(Schema):
    provider = fields.String()
    source_lang = fields.String()
    target_lang = fields.String()
    items = fields.List(fields.Nested(TranslateItemSchema))


class DetectRequestSchema(Schema):
    texts = fields.List(fields.String(), required=True)


class DetectItemSchema(Schema):
    text = fields.String()
    lang = fields.String()


class DetectResponseSchema(Schema):
    items = fields.List(fields.Nested(DetectItemSchema))


class GlossaryUpsertSchema(Schema):
    tenant_id = fields.String(required=True)
    source_lang = fields.String(required=True)
    target_lang = fields.String(required=True)
    pairs = fields.List(fields.Dict(keys=fields.String(), values=fields.String()), load_default=list)


class GlossaryQuerySchema(Schema):
    tenant_id = fields.String(required=True)
    source_lang = fields.String(required=True)
    target_lang = fields.String(required=True)


class GlossaryResponseSchema(Schema):
    tenant_id = fields.String()
    source_lang = fields.String()
    target_lang = fields.String()
    version = fields.Integer()
    pairs = fields.List(fields.Dict(keys=fields.String(), values=fields.String()))


class MessageSchema(Schema):
    message = fields.String()
