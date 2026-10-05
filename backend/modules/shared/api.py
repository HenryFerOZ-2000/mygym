from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from modules.workspaces.policies import parse_uuid


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict) and (unknown := set(data) - set(self.fields)):
            raise serializers.ValidationError(
                {key: ["Campo no permitido."] for key in sorted(unknown)}
            )
        return super().to_internal_value(data)


def find(queryset, identifier):
    item = queryset.filter(pk=parse_uuid(identifier)).first()
    if item is None:
        raise NotFound()
    return item


def page(request, queryset, serialize):
    try:
        number = int(request.query_params.get("page", 1))
        size = min(int(request.query_params.get("page_size", 25)), 100)
        if number < 1 or size < 1:
            raise ValueError
    except ValueError:
        raise ValidationError({"page": "Usa enteros positivos."}) from None
    count = queryset.count()
    start = (number - 1) * size
    if number > 1 and start >= count:
        raise NotFound()
    return {
        "count": count,
        "next": number + 1 if start + size < count else None,
        "previous": number - 1 if number > 1 else None,
        "results": [serialize(item) for item in queryset[start : start + size]],
    }
