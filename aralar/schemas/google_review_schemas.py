from marshmallow import Schema, fields, validate


class ReviewAuthorSchema(Schema):
    name = fields.String(allow_none=True)
    photo_url = fields.String(allow_none=True)
    profile_url = fields.String(allow_none=True)


class ReviewModerationSchema(Schema):
    auto = fields.Boolean()
    reason = fields.String(allow_none=True)
    by = fields.String(allow_none=True)
    at = fields.DateTime(allow_none=True)


class GoogleReviewSchema(Schema):
    _id = fields.String(dump_only=True)
    tenant_id = fields.String()
    provider = fields.String()
    external_id = fields.String()
    rating = fields.Integer()
    text = fields.String()
    language = fields.String(allow_none=True)
    author = fields.Nested(ReviewAuthorSchema)
    published_at = fields.DateTime(allow_none=True)
    status = fields.String()
    moderation = fields.Nested(ReviewModerationSchema)
    is_featured = fields.Boolean()
    display_order = fields.Integer(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class GoogleReviewCreateSchema(Schema):
    """Alta manual de una reseña (provider `manual`)."""

    tenant_id = fields.String(required=True)
    rating = fields.Integer(required=True, validate=validate.Range(min=1, max=5))
    text = fields.String(load_default="")
    language = fields.String(required=False, allow_none=True)
    author = fields.Nested(ReviewAuthorSchema, load_default=dict)
    published_at = fields.DateTime(required=False, allow_none=True)
    external_id = fields.String(required=False)
    is_featured = fields.Boolean(load_default=False)
    display_order = fields.Integer(required=False, allow_none=True)


class GoogleReviewUpdateSchema(Schema):
    """Solo presentación. El contenido lo manda el origen y `status` se cambia
    por `/moderate`."""

    is_featured = fields.Boolean(required=False)
    display_order = fields.Integer(required=False, allow_none=True)


class GoogleReviewModerateSchema(Schema):
    status = fields.String(
        required=True, validate=validate.OneOf(["approved", "pending", "rejected"])
    )


class GoogleReviewListSchema(Schema):
    items = fields.List(fields.Nested(GoogleReviewSchema))
    total = fields.Integer()
    skip = fields.Integer()
    limit = fields.Integer()


class GoogleReviewListQueryArgs(Schema):
    tenant_id = fields.String(required=False)
    provider = fields.String(required=False)
    status = fields.String(
        required=False, validate=validate.OneOf(["approved", "pending", "rejected"])
    )
    rating = fields.Integer(required=False, validate=validate.Range(min=1, max=5))
    skip = fields.Integer(load_default=0)
    limit = fields.Integer(load_default=20)


class GoogleReviewPublicItemSchema(Schema):
    """Tarjeta de reseña para la landing.

    Se exponen nombre y foto del autor porque Google exige atribución visible al
    mostrar reseñas.
    """

    rating = fields.Integer()
    text = fields.String()
    author_name = fields.String(allow_none=True)
    author_photo_url = fields.String(allow_none=True)
    author_profile_url = fields.String(allow_none=True)
    published_at = fields.DateTime(allow_none=True)
    is_featured = fields.Boolean()


class GoogleReviewPublicListSchema(Schema):
    items = fields.List(fields.Nested(GoogleReviewPublicItemSchema))
    total = fields.Integer()
    average_rating = fields.Float(allow_none=True)


class GoogleReviewPublicQueryArgs(Schema):
    tenant_id = fields.String(required=False)
    limit = fields.Integer(required=False)


class GoogleReviewSyncResultSchema(Schema):
    fetched = fields.Integer()
    created = fields.Integer()
    updated = fields.Integer()
    auto_approved = fields.Integer()
    auto_rejected = fields.Integer()  # sin texto: no hay tarjeta que pintar
    pending = fields.Integer()
    errors = fields.List(fields.String())


class GoogleReviewMessageSchema(Schema):
    message = fields.String()
