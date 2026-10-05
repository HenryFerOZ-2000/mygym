from rest_framework import serializers
from modules.shared.api import StrictSerializer


class AttendanceWriteSerializer(StrictSerializer):
    request_id = serializers.UUIDField()
    expected_date = serializers.DateField()
    expected_count = serializers.IntegerField(min_value=0)
    confirm_repeat = serializers.BooleanField(default=False)
    exception = serializers.BooleanField(default=False)
    reason = serializers.CharField(max_length=300, allow_blank=True, default="")


class VoidSerializer(StrictSerializer):
    request_id = serializers.UUIDField()
    reason = serializers.CharField(max_length=300)


class AttendanceReadSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    client_id = serializers.UUIDField()
    full_name = serializers.CharField()
    actor = serializers.CharField()
    created_at = serializers.DateTimeField()
    local_date = serializers.DateField()
    timezone = serializers.CharField()
    decision = serializers.CharField()
    service_status = serializers.CharField()
    reason = serializers.CharField()
    voided = serializers.BooleanField()
    void_reason = serializers.CharField(allow_null=True)
    void_actor = serializers.CharField(allow_null=True)
    voided_at = serializers.DateTimeField(allow_null=True)


class AttendancePreviewSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    full_name = serializers.CharField()
    status = serializers.CharField()
    membership_id = serializers.UUIDField(allow_null=True)
    last_day = serializers.DateField(allow_null=True)
    previous_last_day = serializers.DateField(allow_null=True)
    next_start = serializers.DateField(allow_null=True)
    local_date = serializers.DateField()
    today_count = serializers.IntegerField()
    timezone = serializers.CharField()


class AttendancePageSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = AttendanceReadSerializer(many=True)


class SearchClientSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    full_name = serializers.CharField()
    is_active = serializers.BooleanField()


class SearchPageSerializer(AttendancePageSerializer):
    results = SearchClientSerializer(many=True)


class AttendanceQuerySerializer(StrictSerializer):
    q = serializers.CharField(max_length=120, allow_blank=True, default="")
    date = serializers.DateField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=25)
