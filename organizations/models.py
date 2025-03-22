from django.db import models
from django.conf import settings

import hashlib

class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='organizations_created'
    )
    db_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.db_name

class CustomUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    device_limit = models.PositiveIntegerField(default=5)
    expiration_date = models.DateField()

    def __str__(self):
        return self.user.username

class DeviceType(models.Model):
    name = models.CharField(max_length=100)
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='device_types')

    def __str__(self):
        return f"{self.name}"


class Device(models.Model):
    device_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    serial_number = models.CharField(max_length=255, unique=True)
    device_type = models.ForeignKey(DeviceType, on_delete=models.SET_NULL, null=True)
    exit_password = models.CharField(max_length=255, default="1111")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now=True)
    token = models.CharField(max_length=512, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token and self.name and self.device_type:
            if self.owner and self.serial_number:
                raw_token = f"{self.owner.username}-{self.serial_number}"
                self.token = hashlib.sha256(raw_token.encode()).hexdigest()

        super().save(*args, **kwargs)


    def __str__(self):
        return self.name or "-"

class Media(models.Model):
    MEDIA_TYPES = (('video', 'Video'), ('image', 'Image'))
    media_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to="media/")
    duration = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    media = models.ManyToManyField(Media, through='PlaylistMedia')
    devices = models.ManyToManyField(Device, through='PlaylistDevice')

    def __str__(self):
        return self.name or "-"

class PlaylistMedia(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    media = models.ForeignKey(Media, on_delete=models.CASCADE)

class PlaylistDevice(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
