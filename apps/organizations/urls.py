# organizations/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.organizations.views import (
    DeviceViewSet,
    MediaViewSet,
    OrganizationAdminViewSet,
    PlaylistViewSet,
)

app_name = "organizations"

# User-facing API router
router = DefaultRouter()
router.register(r"devices", DeviceViewSet, basename="device")
router.register(r"playlists", PlaylistViewSet, basename="playlist")
router.register(r"media", MediaViewSet, basename="media")

# Admin API router
admin_router = DefaultRouter()
admin_router.register(
    r"organizations",
    OrganizationAdminViewSet,
    basename="organization",
)

urlpatterns = [
    # Device/player endpoints (legacy paths now backed by ViewSet actions)
    path(
        "playlists/details/",
        DeviceViewSet.as_view({"get": "playlist_detail"}),
        name="playlist_detail",
    ),
    path(
        "register_device/",
        DeviceViewSet.as_view({"post": "create"}),
        name="register_device",
    ),
    path(
        "upload_media/",
        MediaViewSet.as_view({"post": "create"}),
        name="upload_media",
    ),
    path(
        "create_playlist/",
        PlaylistViewSet.as_view({"post": "create"}),
        name="create_playlist",
    ),
    path(
        "sync_device/<str:serial_number>/",
        DeviceViewSet.as_view({"get": "sync"}),
        name="sync_device",
    ),
    # Routers
    path("", include(router.urls)),
    path("admin/", include(admin_router.urls)),
]
