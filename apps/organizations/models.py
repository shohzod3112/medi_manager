import os
import uuid

from django.db import models
from django.conf import settings

import hashlib
from moviepy import VideoFileClip


# class BaseModel(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#
#     class Meta:
#         abstract = True


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    # devices = models.IntegerField(default=0) # counter for device_id like unique for each organization
    # device_limit = models.PositiveIntegerField(default=5)
    # expiration_date = models.DateField()
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
    device_limit = models.PositiveIntegerField(default=5)  # device_limit should be bound to organizations.
    expiration_date = models.DateField()  # expiration subscription should be bound to organizations.

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
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    last_seen = models.DateTimeField(auto_now=True)
    token = models.CharField(max_length=512, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.token and self.name and self.device_type:
            if self.owner and self.serial_number:
                raw_token = f"{self.owner.username}-{self.serial_number}"
                self.token = hashlib.sha256(raw_token.encode()).hexdigest()
        # self.owner.organization.devices += 1
        # self.owner.organization.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name or "-"


class Media(models.Model):
    MEDIA_TYPES = (('video', 'Video'), ('image', 'Image'))
    media_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to="")
    duration = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def get_upload_path(self, filename):
        """Generate upload path: user_uploads/username/filename"""
        if not self.owner_id:
            raise ValueError("Owner must be set before saving file")
        return f"{self.owner.username}/{filename}"

    def save(self, *args, **kwargs):
        if not self.owner_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.owner = User.objects.get(pk=1)

        if self.file and not self.file.name.startswith(f'{self.owner.username}/'):
            original_filename = os.path.basename(self.file.name)
            self.file.name = self.get_upload_path(original_filename)

        super().save(*args, **kwargs)
        if self.type == "image" and self.file:
            media = self.file.url.split("/")[-1]
            if media == "mp4":
                self.type = "video"
                super().save(update_fields=["type"])
            elif self.duration is not None:
                self.duration = None
                super().save(update_fields=["duration"])

        if self.type == "video" and self.file:
            file_path = self.file.path
            try:
                clip = VideoFileClip(file_path)
                duration_seconds = int(clip.duration)
                clip.close()

                if self.duration != duration_seconds:
                    self.duration = duration_seconds
                    self.type = "video"
                    super().save(update_fields=["duration", "type"])
            except Exception as e:
                print(f"Error getting video duration: {e}")


class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    media = models.ManyToManyField(Media)
    devices = models.ManyToManyField(Device)

    def __str__(self):
        return self.name or "-"
