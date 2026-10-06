import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.views.decorators.http import require_safe


@require_safe
def index(request):
    path = Path(settings.LOCAL_FRONTEND_DIST) / "index.html"
    if not path.is_file():
        raise Http404
    response = FileResponse(path.open("rb"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_safe
def asset(request, name):
    root = (Path(settings.LOCAL_FRONTEND_DIST) / "assets").resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise Http404
    content_type = {".js": "text/javascript", ".css": "text/css"}.get(path.suffix)
    response = FileResponse(
        path.open("rb"),
        content_type=content_type
        or mimetypes.guess_type(path)[0]
        or "application/octet-stream",
    )
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    response["X-Content-Type-Options"] = "nosniff"
    return response
