from rest_framework import serializers
from .models import ClientRecord


class ClientWriteSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=254, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {key: ["Campo no permitido."] for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


class ClientReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientRecord
        fields = [
            "id",
            "full_name",
            "phone",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ClientPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ClientReadSerializer(many=True)
