from calendar import monthrange
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework.exceptions import ValidationError


def today(workspace):
    return timezone.now().astimezone(ZoneInfo(workspace.timezone)).date()


def period_end(start, unit, quantity):
    try:
        if unit == "DAYS":
            return start + timedelta(days=quantity)
        months = start.year * 12 + start.month - 1 + quantity
        year, month = divmod(months, 12)
        return date(year, month + 1, min(start.day, monthrange(year, month + 1)[1]))
    except (ValueError, OverflowError):
        raise ValidationError(
            {"start_date": "Fecha fuera del rango admitido."}
        ) from None
