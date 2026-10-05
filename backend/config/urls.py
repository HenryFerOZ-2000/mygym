from django.urls import include, path
from config.health import health
from modules.workspaces.api import WorkspacesView
from modules.clients.api import ClientListView, ClientDetailView

urlpatterns = [
    path("api/v1/health/", health),
    path("api/v1/auth/", include("modules.identity.urls")),
]
urlpatterns += [
    path("api/v1/workspaces/<str:workspace_id>/", include("modules.gym.urls")),
    path("api/v1/me/workspaces/", WorkspacesView.as_view()),
    path("api/v1/workspaces/<str:workspace_id>/clients/", ClientListView.as_view()),
    path(
        "api/v1/workspaces/<str:workspace_id>/clients/<str:client_id>/",
        ClientDetailView.as_view(),
    ),
]
handler404 = "config.errors.not_found"
handler500 = "config.errors.server_error"
