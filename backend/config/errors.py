from django.http import JsonResponse
from rest_framework.views import exception_handler as drf_exception_handler


def error_body(code, message, fields=None):
    return {"error": {"code": code, "message": message, "fields": fields or {}}}


def csrf_failure(request, reason=""):
    return JsonResponse(
        error_body(
            "csrf_failed", "No se pudo validar la solicitud. Actualiza la página."
        ),
        status=403,
    )


def not_found(request, exception=None):
    return JsonResponse(error_body("not_found", "Recurso no disponible."), status=404)


def server_error(request):
    return JsonResponse(
        error_body("server_error", "No se pudo completar la solicitud."), status=500
    )


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    codes = {
        400: "validation_error",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        415: "unsupported_media_type",
    }
    messages = {
        400: "Revisa los datos de la solicitud.",
        403: "No tienes permiso para esta acción.",
        404: "Recurso no disponible.",
        405: "Operación no disponible.",
    }
    data = response.data
    fields = data if isinstance(data, dict) and "detail" not in data else {}
    response.data = error_body(
        codes.get(response.status_code, "request_failed"),
        messages.get(response.status_code, "No se pudo completar la solicitud."),
        fields,
    )
    return response
