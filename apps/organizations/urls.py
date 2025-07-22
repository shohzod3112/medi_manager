# organizations/urls.py
from django.urls import path

from apps.organizations.views import PlaylistsDetailAPIView, GetDeviceToken, RegisterDeviceView, Upload_media, \
    create_playlist, sync_device

urlpatterns = [
    path('playlist_detail/', PlaylistsDetailAPIView.as_view(), name='playlist_detail'),
    path('get_device_token/', GetDeviceToken.as_view(), name="get_device_token"),
    path('register_device/', RegisterDeviceView.as_view(), name='register_device'),
    path('upload_media/', Upload_media.as_view(), name='upload_media'),
    path('create_playlist/', create_playlist, name='create_playlist'),
    path('sync_device/<str:serial_number>/', sync_device, name='sync_device'),
]
