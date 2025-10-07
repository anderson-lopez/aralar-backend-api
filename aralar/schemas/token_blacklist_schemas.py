from marshmallow import Schema, fields


class LogoutSchema(Schema):
    """Schema para logout request"""
    # No necesita campos adicionales, el token viene en el header Authorization
    pass


class LogoutResponseSchema(Schema):
    """Schema para logout response"""
    message = fields.Str(required=True)
    blacklisted_at = fields.DateTime(required=True)


class InvalidateTokenSchema(Schema):
    """Schema para invalidar token por admin"""
    token = fields.Str(required=True)
    reason = fields.Str(required=False, load_default="admin_action")


class InvalidateTokenResponseSchema(Schema):
    """Schema para respuesta de invalidación de token"""
    message = fields.Str(required=True)
    jti = fields.Str(required=True)
    reason = fields.Str(required=True)
    blacklisted_at = fields.DateTime(required=True)


class BlacklistHistoryItemSchema(Schema):
    """Schema para un item del historial de blacklist"""
    jti = fields.Str(required=True)
    blacklisted_at = fields.DateTime(required=True)
    expires_at = fields.DateTime(required=True)
    reason = fields.Str(required=True)


class BlacklistHistoryResponseSchema(Schema):
    """Schema para respuesta del historial de blacklist"""
    user_id = fields.Str(required=True)
    tokens = fields.List(fields.Nested(BlacklistHistoryItemSchema), required=True)
    total_count = fields.Int(required=True)


class BlacklistStatsSchema(Schema):
    """Schema para estadísticas de blacklist"""
    total_blacklisted = fields.Int(required=True)
    by_reason = fields.List(fields.Dict(), required=True)


class BlacklistMaintenanceResponseSchema(Schema):
    """Schema para respuesta de mantenimiento de blacklist"""
    message = fields.Str(required=True)
    cleaned_expired_tokens = fields.Int(required=True)
    current_stats = fields.Nested(BlacklistStatsSchema, required=True)


class TokenValidationErrorSchema(Schema):
    """Schema para errores de validación de tokens"""
    message = fields.Str(required=True)
    error = fields.Str(required=True)
    code = fields.Int(required=True)
