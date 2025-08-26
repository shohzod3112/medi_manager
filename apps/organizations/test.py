# organizations/tests.py
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Device, Media, Playlist


class OrganizationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser",
            password="password123",
        )
        self.client.login(username="testuser", password="password123")
        self.device_data = {
            "name": "Test Device",
            "serial_number": "ABC123",
            "exit_password": "securepass",
            "owner": self.user.id,
        }

    def test_register_device(self):
        response = self.client.post(
            "/api/organizations/register_device/",
            self.device_data,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Device.objects.count(), 1)

    def test_upload_media(self):
        media_data = {"name": "Test Video", "type": "video", "owner": self.user.id}
        response = self.client.post("/api/organizations/upload_media/", media_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Media.objects.count(), 1)

    def test_create_playlist(self):
        playlist_data = {
            "name": "Test Playlist",
            "owner": self.user.id,
            "start_time": "2025-03-07T10:00:00Z",
            "end_time": "2025-03-07T12:00:00Z",
        }
        response = self.client.post(
            "/api/organizations/create_playlist/",
            playlist_data,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Playlist.objects.count(), 1)

    def test_sync_device(self):
        Device.objects.create(
            name="Test Device",
            serial_number="ABC123",
            exit_password="securepass",
            owner=self.user,
        )
        response = self.client.get("/api/organizations/sync_device/ABC123/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("playlists", response.data)
