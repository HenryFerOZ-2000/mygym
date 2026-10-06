from django.urls import path, re_path

from config.local_views import asset, index
from config.urls import urlpatterns as api_patterns

urlpatterns = [
    *api_patterns,
    path("", index),
    path("login", index),
    path("workspaces", index),
    re_path(r"^workspaces/[^/]+/(?:clients|plans|attendance|reports)$", index),
    re_path(r"^workspaces/[^/]+/clients/[^/]+/account$", index),
    path("assets/<path:name>", asset),
]
handler404 = "config.errors.not_found"
handler500 = "config.errors.server_error"
