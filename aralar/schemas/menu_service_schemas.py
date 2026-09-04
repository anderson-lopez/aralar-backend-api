from marshmallow import Schema, fields


class MenuServiceCreateSchema(Schema):
    tenant_id = fields.String(required=True)
    slug = fields.String(required=True)  # estable, único por tenant (ej. "desayunos")
    name = fields.String(required=True)  # nombre interno para la administración
    labels = fields.Dict(load_default=dict)  # nombre público i18n: {"es-ES": "Desayunos", ...}
    order = fields.Integer(load_default=0)  # orden de aparición en la sección
    is_active = fields.Boolean(load_default=True)


class MenuServiceUpdateSchema(Schema):
    # OJO: `slug` es INMUTABLE y por eso no está aquí. Los menús lo referencian
    # en `service_slugs` sin cascada; renombrarlo los dejaría huérfanos.
    name = fields.String(required=False)
    labels = fields.Dict(required=False)
    order = fields.Integer(required=False)
    is_active = fields.Boolean(required=False)


class MenuServiceSchema(Schema):
    _id = fields.String(dump_only=True)
    tenant_id = fields.String()
    slug = fields.String()
    name = fields.String()
    labels = fields.Dict()
    order = fields.Integer()
    is_active = fields.Boolean()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    # Solo presente al desactivar un servicio con menús: cuántos quedan ocultos.
    affected_menus = fields.Integer(dump_only=True)


class MenuServiceListSchema(Schema):
    items = fields.List(fields.Nested(MenuServiceSchema))
    total = fields.Integer()


class MenuServiceListQueryArgs(Schema):
    tenant_id = fields.String(required=False)
    is_active = fields.Boolean(required=False)


class MenuServiceMessageSchema(Schema):
    message = fields.String()


class MenuServicePublicItemSchema(Schema):
    """Item de la sección pública "Otros servicios"."""

    slug = fields.String()
    name = fields.String()
    label = fields.String(allow_none=True)  # etiqueta resuelta por idioma (cae a name)
    order = fields.Integer()


class MenuServicePublicListSchema(Schema):
    items = fields.List(fields.Nested(MenuServicePublicItemSchema))


class MenuServicePublicQueryArgs(Schema):
    tenant_id = fields.String(required=False)
    locale = fields.String(required=False)
