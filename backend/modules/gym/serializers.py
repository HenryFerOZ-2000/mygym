from rest_framework import serializers
from modules.shared.api import StrictSerializer


class PlanWriteSerializer(StrictSerializer):
    name = serializers.CharField(max_length=120)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    currency = serializers.RegexField(r"^[A-Z]{3}$")
    unit = serializers.ChoiceField(choices=["DAYS", "MONTHS"])
    quantity = serializers.IntegerField(min_value=1, max_value=3650)
    is_active = serializers.BooleanField(default=True)
    is_promotion = serializers.BooleanField(default=False)
    available_from = serializers.DateField(allow_null=True, default=None)
    available_until = serializers.DateField(allow_null=True, default=None)


class PlanPatchSerializer(PlanWriteSerializer):
    expected_version = serializers.IntegerField(min_value=1)


class PlanReadSerializer(PlanWriteSerializer):
    id = serializers.UUIDField()
    version = serializers.IntegerField()


class PlanPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = PlanReadSerializer(many=True)


class PreviewSerializer(StrictSerializer):
    plan_id = serializers.UUIDField()
    start_date = serializers.DateField()


class EnrollmentSerializer(PreviewSerializer):
    request_id = serializers.UUIDField()
    expected_version = serializers.IntegerField(min_value=1)
    expected_start = serializers.DateField()
    expected_end = serializers.DateField()


class PreviewReadSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    version = serializers.IntegerField()
    name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    last_day = serializers.DateField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()


class MembershipReadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    version = serializers.IntegerField()
    amount = serializers.CharField()
    currency = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    last_day = serializers.DateField(allow_null=True)
    cancelled_on = serializers.DateField(allow_null=True)
    status = serializers.CharField()
    remaining_days = serializers.IntegerField()
    freezes = serializers.ListField(child=serializers.DictField())
    changes = serializers.ListField(child=serializers.DictField())


class MembershipPageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = MembershipReadSerializer(many=True)


class ChangeSerializer(StrictSerializer):
    request_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=300)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class CancelSerializer(StrictSerializer):
    request_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=300)
    effective_date = serializers.DateField()
