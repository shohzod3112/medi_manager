# organizations/urls.py
from django.urls import path
from apps.organizations import views

app_name = "organizations"

urlpatterns = [
    path(f"{app_name}", views.OrganizationListCreateView.as_view(), name="organization-list-create"),
    path(f"{app_name}/<int:pk>", views.OrganizationRetrieveUpdateDestroyView.as_view(), name="organization-detail"),
    # path(f"{app_name}/<int:pk>/assign-user", views.AssignUserToOrganizationView.as_view(), name="organization-assign-user"),
    # path(f"{app_name}/<int:pk>/unassign-user", views.UnassignUserFromOrganizationView.as_view(), name="organization-unassign-user"),
    path(f"{app_name}/select", views.OrganizationSelectListAPIView.as_view()),

    path(f"{app_name}/device-handshake", views.DeviceHandshakeView.as_view()),
    path(f"{app_name}/device-select", views.DeviceSelectListAPIView.as_view()),
    path(f"{app_name}/devices", views.DeviceListCreateAPIView.as_view(), name="device-list-create"),
    path(f"{app_name}/devices/<int:pk>", views.DeviceRetrieveUpdateDestroyAPIView.as_view(), name="device-list-create"),

    path(f"{app_name}/devices/get-token/<str:serial_number>", views.DeviceDetailAPIView.as_view(), name="device-detail"),
    path(f"{app_name}/devices/<str:serial_number>/sync", views.DeviceSyncAPIView.as_view(), name="device-sync"),
    path(f"{app_name}/devices/playlist-detail", views.PlaylistDetailAPIView.as_view(), name="playlist-detail"),

    path(f"{app_name}/playlists", views.PlaylistListCreateView.as_view(), name="playlist-list-create"),
    path(f"{app_name}/playlists/<int:pk>", views.PlaylistDetailView.as_view(), name="playlist-detail"),
    path(f"{app_name}/playlists/set-devices/<int:pk>", views.PlaylistSetDevicesAPIView.as_view(), name="playlist-detail"),

    path(f"{app_name}/file-select", views.FileSelectListAPIView.as_view()),
    path(f"{app_name}/file", views.FileListCreateView.as_view(), name="file-list-create"),
    path(f"{app_name}/file/<int:pk>", views.FileDetailView.as_view(), name="file-detail"),

    path(f"{app_name}/device-types", views.DeviceTypeListCreateView.as_view()),
    path(f"{app_name}/device-types-select", views.DeviceTypeSelectListAPIView.as_view()),
    path(f"{app_name}/device-types/<int:pk>", views.DeviceTypeRetrieveUpdateDestroyAPIView.as_view()),

    path(f"{app_name}/device-groups/", views.DeviceGroupListCreateAPIView.as_view()),
    path(f"{app_name}/device-groups/select/", views.DeviceGroupListSelectAPIView.as_view()),
    path(f"{app_name}/device-groups/<int:pk>/", views.DeviceGroupRetrieveUpdateDestroyAPIView.as_view()),
    path(f"{app_name}/device-groups/remove-devices/", views.DeviceGroupRemoveDevicesAPIView.as_view()),
]
