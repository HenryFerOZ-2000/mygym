from decimal import Decimal
from rest_framework import serializers
from modules.shared.api import StrictSerializer


class AllocationSerializer(StrictSerializer):
    charge_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )


class PaymentSerializer(StrictSerializer):
    request_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    currency = serializers.RegexField(r"^[A-Z]{3}$")
    method = serializers.ChoiceField(choices=["CASH", "TRANSFER"])
    allocations = AllocationSerializer(many=True, min_length=1, max_length=50)


class RefundSerializer(StrictSerializer):
    request_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=300)
    allocations = AllocationSerializer(many=True, min_length=1, max_length=50)


class PaymentReadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    amount = serializers.CharField()
    currency = serializers.CharField()
    method = serializers.CharField()
    created_at = serializers.DateTimeField()
    allocations = serializers.ListField(child=serializers.DictField())
    refunds = serializers.ListField(child=serializers.DictField())


class ChargeReadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    source = serializers.UUIDField()
    label = serializers.CharField()
    amount = serializers.CharField()
    balance = serializers.CharField()
    currency = serializers.CharField()
    created_at = serializers.DateTimeField()


class ChargePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = ChargeReadSerializer(many=True)


class PaymentPageSerializer(ChargePageSerializer):
    results = PaymentReadSerializer(many=True)


class RefundReadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    amount = serializers.CharField()
