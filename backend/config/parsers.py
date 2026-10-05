import io
from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser


class BoundedJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        raw = stream.read(settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1)
        if len(raw) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
            raise ValidationError({"body": ["La solicitud es demasiado grande."]})
        return super().parse(io.BytesIO(raw), media_type, parser_context)
