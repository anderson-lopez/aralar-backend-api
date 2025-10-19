from marshmallow import Schema, fields, validate, validates_schema, ValidationError
from datetime import datetime, time
from typing import List
from werkzeug.exceptions import abort


class SchedulingSchema(Schema):
    """Schema para las reglas de programación de notificaciones"""
    start_date = fields.DateTime(required=True)
    end_date = fields.DateTime(required=True)
    days_of_week = fields.List(
        fields.String(validate=validate.OneOf(['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'])),
        load_default=[]
    )
    time_start = fields.String(
        validate=validate.Regexp(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', error="Time must be in HH:MM format"),
        allow_none=True
    )
    time_end = fields.String(
        validate=validate.Regexp(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', error="Time must be in HH:MM format"),
        allow_none=True
    )

    @validates_schema
    def validate_scheduling(self, data, **kwargs):
        """Validar las reglas de scheduling"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        time_start = data.get('time_start')
        time_end = data.get('time_end')
        
        # Validar que end_date sea posterior o igual a start_date
        if start_date and end_date and end_date < start_date:
            abort(400, description="end_date must be after or equal to start_date")
        
        # Validar horas si están presentes
        if time_start and time_end:
            # Si las fechas son el mismo día, time_end debe ser posterior a time_start
            if start_date and end_date:
                start_date_only = start_date.date()
                end_date_only = end_date.date()
                
                if start_date_only == end_date_only:
                    # Mismo día: time_end debe ser posterior a time_start
                    try:
                        start_time = datetime.strptime(time_start, '%H:%M').time()
                        end_time = datetime.strptime(time_end, '%H:%M').time()
                        
                        if end_time <= start_time:
                            abort(400, description="time_end must be after time_start when scheduling is on the same day")
                    except ValueError:
                        abort(400, description="Invalid time format")
                else:
                    # Diferentes días: time_end puede ser anterior a time_start
                    pass


class DisplayStyleSchema(Schema):
    """Schema para los estilos de visualización"""
    background_color = fields.String(
        validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$', error="Background color must be a valid hex color"),
        load_default='#FFFFE0'
    )
    text_color = fields.String(
        validate=validate.Regexp(r'^#[0-9A-Fa-f]{6}$', error="Text color must be a valid hex color"),
        load_default='#000000'
    )
    custom_css_class = fields.String(allow_none=True)


class DisplaySchema(Schema):
    """Schema para la configuración de visualización"""
    location = fields.String(
        required=True,
        validate=validate.OneOf([
            'top-bar', 'hero-section', 'menu-section', 
            'contact-section', 'footer', 'global-modal', 'global-toast'
        ])
    )
    type = fields.String(
        required=True,
        validate=validate.OneOf(['banner', 'card', 'modal', 'toast'])
    )
    style = fields.Nested(DisplayStyleSchema, load_default={})


class I18NSchema(Schema):
    """Schema para configuración i18n de notificaciones"""
    default_locale = fields.String(required=True)
    locales = fields.List(fields.String(), load_default=list)


class NotificationCreateSchema(Schema):
    """Schema para crear notificaciones"""
    name = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters")
    )
    is_active = fields.Boolean(load_default=True)
    priority = fields.Integer(
        validate=validate.Range(min=1, max=100, error="Priority must be between 1 and 100"),
        load_default=1
    )
    scheduling = fields.Nested(SchedulingSchema, required=True)
    display = fields.Nested(DisplaySchema, required=True)
    locales = fields.Dict(
        keys=fields.String(),
        values=fields.Dict(),
    )
    i18n = fields.Nested(I18NSchema, required=True)


class NotificationUpdateSchema(Schema):
    """Schema para actualizar notificaciones"""
    name = fields.String(
        validate=validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters")
    )
    is_active = fields.Boolean()
    priority = fields.Integer(
        validate=validate.Range(min=1, max=100, error="Priority must be between 1 and 100")
    )
    scheduling = fields.Nested(SchedulingSchema)
    display = fields.Nested(DisplaySchema)
    locales = fields.Dict(
        keys=fields.String(),
        values=fields.Dict(),
    )
    i18n = fields.Nested(I18NSchema)


class NotificationOutSchema(Schema):
    """Schema para respuesta de notificaciones"""
    id = fields.String(attribute="_id")
    name = fields.String()
    is_active = fields.Boolean()
    priority = fields.Integer()
    scheduling = fields.Nested(SchedulingSchema)
    display = fields.Nested(DisplaySchema)
    locales = fields.Dict(keys=fields.String(), values=fields.Dict())
    i18n = fields.Nested(I18NSchema)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class NotificationListResponseSchema(Schema):
    """Schema para lista de notificaciones"""
    items = fields.List(fields.Nested(NotificationOutSchema))
    total = fields.Integer()


class NotificationCreateResponseSchema(Schema):
    """Schema para respuesta de creación"""
    id = fields.String()
    message = fields.String()


class NotificationLocaleDataSchema(Schema):
    content = fields.String(required=True, validate=validate.Length(min=1, max=2000))


class NotificationLocaleUpdateSchema(Schema):
    data = fields.Nested(NotificationLocaleDataSchema, required=True)
    meta = fields.Dict(required=False)
