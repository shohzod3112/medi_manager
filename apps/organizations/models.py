import hashlib
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.timezone import now

from apps.organizations.exseptions.limit import DeviceLimitReached
from attachment.models import Attachment


class BaseModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Organization(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    # Device management
    device_limit = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of devices allowed for this organization",
    )
    current_device_count = models.PositiveIntegerField(
        default=0,
        help_text="Current number of devices in use",
    )
    next_device_id = models.PositiveIntegerField(
        default=1,
        help_text="Next available device ID for this organization",
    )

    # Organization settings
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="Organization subscription expiration date",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this organization is active",
    )
    expiration_task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        app_label = "organizations"
        ordering = ["name"]
        db_table = "organizations"
        verbose_name_plural = "Organizations"
        verbose_name = "Organization"

    def __str__(self):
        return self.name

    # def save(self, *args, **kwargs):
    #     # Generate slug if not provided
    #     if not self.slug and self.name:
    #         self.slug = self.name.lower().replace(" ", "-")
    #     super().save(*args, **kwargs)

    def get_total_used_devices(self):
        """Get total devices used by all users in this organization"""
        return self.device_count()

    def get_available_device_slots(self):
        """Get available device slots"""
        return self.device_limit - self.get_total_used_devices()

    def can_add_device(self):
        """Check if organization can add another device"""
        return self.get_available_device_slots() > 0

    def get_next_device_id(self):
        """Get next available device ID and increment counter"""
        device_id = self.next_device_id
        self.next_device_id += 1
        self.save(update_fields=["next_device_id"])
        return device_id

    def is_expired(self):
        """Check if organization subscription is expired"""
        if self.expiration_date:
            return self.expiration_date < now().date()
        return False

    def get_user_count(self):
        """Get number of users in this organization"""
        return self.users.count()

    def get_active_user_count(self):
        """Get number of active users in this organization"""
        return self.users.filter(is_active=True).count()

    def device_count(self):
        return self.devices.count()

    def has_reached_device_limit(self):
        if self.device_limit == 0:
            return False
        return self.device_count() >= self.device_limit


class OrgCounter(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='counters')
    key = models.CharField(max_length=50)  # model nomi: device, file, playlist
    last = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('organization', 'key')

    def __str__(self):
        return f"{self.organization_id}:{self.key} -> {self.last}"


class PerOrgSequential(models.Model):
    """
    Abstract mixin for sequential local_id inside organization.
    """
    local_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        unique_together = ('organization', 'local_id')

    def get_counter_key(self):
        # default: model nomi
        return self._meta.model_name

    def save(self, *args, **kwargs):
        if self.local_id:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            counter, _ = OrgCounter.objects.select_for_update().get_or_create(
                organization=self.organization,
                key=self.get_counter_key()
            )
            counter.last += 1
            self.local_id = counter.last
            super().save(*args, **kwargs)
            counter.save(update_fields=['last'])


class DeviceType(BaseModel):
    """Device type model for categorizing devices"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "device_types"
        verbose_name_plural = "Device Types"
        verbose_name = "Device Type"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DeviceQuerySet(models.QuerySet):
    def create(self, **kwargs):
        owner = kwargs.pop("owner", None)
        if owner is not None:
            # Auto-provision organization and user_profile from owner for backward compatibility in tests
            # from apps.users.models import UserProfile

            # Ensure default organization exists
            org, _ = Organization.objects.get_or_create(
                name="test_org",
                defaults={"description": "Auto provisioned"},
            )
            # profile, _ = UserProfile.objects.get_or_create(
            #     user=owner,
            #     defaults={"organization": org},
            # )
            # if not profile.organization_id:
            #     profile.organization = org
            #     profile.save(update_fields=["organization"])
            # kwargs.setdefault("user_profile", profile)
            # kwargs.setdefault("organization", profile.organization)
        return super().create(**kwargs)


class Device(PerOrgSequential, BaseModel):
    # Use custom queryset/manager to support legacy create(owner=...) paths in tests
    objects = DeviceQuerySet.as_manager()

    organization_device_id = models.PositiveIntegerField(
        help_text="Device ID within the organization (starts from 1)",
    )

    name = models.CharField(max_length=255, blank=True)
    serial_number = models.CharField(max_length=255, unique=True)
    device_type = models.ForeignKey(
        DeviceType,
        on_delete=models.SET_NULL,
        null=True,
        related_name="devices",
    )

    # Security
    exit_password = models.CharField(max_length=255, default="1111")
    token = models.CharField(max_length=512, blank=True, null=True)

    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="devices",
    )

    # Status and tracking
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "devices"
        verbose_name_plural = "Devices"
        verbose_name = "Device"
        ordering = ["organization", "organization_device_id"]
        unique_together = [["organization", "organization_device_id"]]

    def __str__(self):
        return f"{self.organization.name} - Device {self.organization_device_id} ({self.name or self.serial_number})"

    def clean(self):
        # """Validate device creation"""
        if not self.pk:  # New device
            # Check if organization can add more devices
            if not self.organization.can_add_device():
                raise ValidationError(
                    f"Organization {self.organization.name} has reached its device limit of {self.organization.device_limit}",
                )

    def save(self, *args, **kwargs):
        if not self.pk:  # New device
            self.clean()
            # Assign organization-specific device ID
            if not self.organization_device_id:
                self.organization_device_id = self.organization.get_next_device_id()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Decrement users's device count
        # self.user_profile.remove_device()
        super().delete(*args, **kwargs)

    # def get_full_device_id(self):
    #     """Get full device identifier"""
    #     return f"{self.organization.slug}-{self.organization_device_id}"


class File(PerOrgSequential, BaseModel):
    """Media model for storing video and image files"""

    FILE_TYPES = (("video", "Video"), ("image", "Image"))

    file_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    type = models.CharField(max_length=10, choices=FILE_TYPES)
    attachment = models.ForeignKey(Attachment, on_delete=models.SET_NULL, null=True, related_name="files")
    is_widget = models.BooleanField(default=False)
    config = models.JSONField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)

    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="files",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="files",
    )

    class Meta:
        db_table = "media"
        verbose_name_plural = "Files"
        verbose_name = "File"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_id} - {self.attachment.name if self.attachment else ''}"

    def save(self, *args, **kwargs):

        if not self.owner_id:
            raise ValueError("Owner va organization bo‘lishi kerak")
        else:
            self.organization = self.owner.organization

        # Detect file type by file extension
        if self.attachment:
            ext = os.path.splitext(self.attachment.file.name)[1].lower()
            if ext in [
                ".apng", ".png", ".avif", ".gif", ".jpg", ".jpeg",
                ".jfif", ".pjpeg", ".pjp", ".png", ".svg", ".webp",
                ".bmp", ".ico", ".cur", ".tif", ".tiff", ".heif", ".heic"
            ]:
                self.type = "image"
                self.duration = None  # Images don't have duration
            elif ext in [
                ".m4v", ".mp4", ".m4p", ".mov", ".qt", ".wmv", ".avi", ".mkv",
                " .webm", ".flv", ".f4v", ".f4p", ".f4a" ,".f4b", ".3gp", ".3g2",
                ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".m2v", ".vob", ".ts",
                ".mts", ".m2ts", ".ogv", ".ogg", ".gifv", ".mng", ".yuv", ".rm",
                ".rmvb", ".viv", ".asf", ".amv", ".svi", ".mxf", ".roq", ".nsv", ".rrc", "mod"
            ]:
                self.type = "video"
            else:
                raise ValidationError(f"Unsupported file type: {ext}")

        super().save(*args, **kwargs)

        # If video, extract duration
        if self.type == "video":
            try:
                # Lazy import to avoid import-time errors and support multiple MoviePy layouts
                _VFC = None
                try:
                    from moviepy.editor import VideoFileClip as _VFC
                except Exception:
                    try:
                        from moviepy import VideoFileClip as _VFC
                    except Exception:
                        _VFC = None
                if _VFC:
                    clip = _VFC(self.attachment.file.path)
                    duration_seconds = int(getattr(clip, "duration", 0) or 0)
                    clip.close()

                    if self.duration != duration_seconds:
                        self.duration = duration_seconds
                        super().save(update_fields=["duration"])
            except Exception as e:
                print(f"Error getting video duration: {e}")

    def delete(self, *args, **kwargs):
        # O‘chiriladigan faylga bog‘langan attachmentni eslab qolamiz
        attachment = self.attachment

        # Fayl yozuvini o‘chiramiz
        super().delete(*args, **kwargs)


class Playlist(PerOrgSequential, BaseModel):
    PLAYLIST_TYPE_CHOICES = [
        ("event", "Event"),
        ("permanent", "Permanent"),
    ]

    playlist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    playlist_type = models.CharField(
        max_length=20, choices=PLAYLIST_TYPE_CHOICES, default="permanent"
    )

    # Timing
    start_date = models.DateField(null=True, blank=True)   # Event uchun
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    # Relationships
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="playlists",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="playlists",
    )
    file = models.ManyToManyField(File, related_name="playlists")
    devices = models.ManyToManyField(Device, related_name="playlists")

    # Status
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "playlists"
        verbose_name_plural = "Playlists"
        verbose_name = "Playlist"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def get_duration(self):
        """Get playlist duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0

    def is_currently_active(self):
        """Check if playlist is currently active"""
        current_time = timezone.now()
        return self.start_time <= current_time <= self.end_time
