from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from rest_framework import serializers

from .api import StrictSerializer


class ReportRangeSerializer(StrictSerializer):
    from_date = serializers.DateField()
    to_date = serializers.DateField()

    def validate(self, data):
        start, end = data["from_date"], data["to_date"]
        if end < start or (end - start).days >= 366 or end == date.max:
            raise serializers.ValidationError("Seleccione un rango de 1 a 366 días.")
        return data


def period_bounds(start, end, zone):
    tz = ZoneInfo(zone)
    return (
        datetime.combine(start, time.min, tz),
        datetime.combine(end + timedelta(days=1), time.min, tz),
    )
