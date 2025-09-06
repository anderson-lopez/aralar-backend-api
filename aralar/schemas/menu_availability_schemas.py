from marshmallow import Schema, fields, validates, validates_schema, ValidationError, validate
from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DOW = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


class DateRangeSchema(Schema):
    start = fields.Date(required=True)  # "YYYY-MM-DD"
    end = fields.Date(required=True)

    @validates_schema
    def _check_order(self, data, **kwargs):
        s, e = data.get("start"), data.get("end")
        if s and e and s > e:
            raise ValidationError("start must be <= end", field_name="end")


class AvailabilitySchema(Schema):
    timezone = fields.String(required=True)
    days_of_week = fields.List(fields.String(validate=validate.OneOf(DOW)), required=True)
    date_ranges = fields.List(
        fields.Nested(DateRangeSchema), required=True, validate=validate.Length(min=1)
    )

    @validates("timezone")
    def _valid_tz(self, tzname):
        try:
            ZoneInfo(tzname)
        except ZoneInfoNotFoundError:
            raise ValidationError("Invalid IANA timezone (e.g. Europe/Madrid)")
