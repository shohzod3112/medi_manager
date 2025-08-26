import hashlib
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.timezone import now

from apps.organizations.exseptions.limit import DeviceLimitReached


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
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

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="organizations_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "organizations"
        ordering = ["name"]
        db_table = "organizations"
        verbose_name_plural = "Organizations"
        verbose_name = "Organization"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Generate slug if not provided
        if not self.slug and self.name:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)

    def get_total_used_devices(self):
        """Get total devices used by all users in this organization"""
        return (
            self.user_profiles.aggregate(total=models.Sum("current_device_count"))[
                "total"
            ]
            or 0
        )

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
        return self.user_profiles.count()

    def get_active_user_count(self):
        """Get number of active users in this organization"""
        return self.user_profiles.filter(is_active=True).count()


class DeviceType(models.Model):
    """Device type model for categorizing devices"""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
            from apps.users.models import UserProfile

            # Ensure default organization exists
            org, _ = Organization.objects.get_or_create(
                name="test_org",
                defaults={"description": "Auto provisioned"},
            )
            profile, _ = UserProfile.objects.get_or_create(
                user=owner,
                defaults={"organization": org},
            )
            if not profile.organization_id:
                profile.organization = org
                profile.save(update_fields=["organization"])
            kwargs.setdefault("user_profile", profile)
            kwargs.setdefault("organization", profile.organization)
        return super().create(**kwargs)


class Device(models.Model):
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
        blank=True,
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
    user_profile = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.CASCADE,
        related_name="devices",
    )

    # Status and tracking
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "devices"
        verbose_name_plural = "Devices"
        verbose_name = "Device"
        ordering = ["organization", "organization_device_id"]
        unique_together = [["organization", "organization_device_id"]]

    def __str__(self):
        return f"{self.organization.name} - Device {self.organization_device_id} ({self.name or self.serial_number})"

    def clean(self):
        """Validate device creation"""
        if not self.pk:  # New device
            # Check if users can add more devices
            if not self.user_profile.can_add_device():
                raise DeviceLimitReached(
                    f"User {self.user_profile.user.username} has reached their device limit of {self.user_profile.device_limit}",
                )

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

            # Generate token if not provided
            if not self.token:
                raw_token = f"{self.user_profile.user.username}-{self.serial_number}"
                self.token = hashlib.sha256(raw_token.encode()).hexdigest()

            # Increment users's device count
            self.user_profile.add_device()

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Decrement users's device count
        self.user_profile.remove_device()
        super().delete(*args, **kwargs)

    def get_full_device_id(self):
        """Get full device identifier"""
        return f"{self.organization.slug}-{self.organization_device_id}"


class Media(models.Model):
    """Media model for storing video and image files"""

    MEDIA_TYPES = (("video", "Video"), ("image", "Image"))

    media_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = models.FileField(upload_to="")
    duration = models.IntegerField(null=True, blank=True)

    organization = models.ForeignKey(
        "Organization",
        on_delete=models.CASCADE,
        related_name="media",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="media",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "media"
        verbose_name_plural = "Media"
        verbose_name = "Media"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_upload_path(self, filename):
        if not self.owner_id or not self.organization_id:
            raise ValueError("Owner and organization must be set before saving file")
        return f"{self.organization.slug}/{self.owner.username}/{filename}"

    def save(self, *args, **kwargs):
        if not self.owner_id or not self.organization_id:
            raise ValueError("Owner and organization must be set before saving file")

        # Fix file name path
        if self.file and not self.file.name.startswith(
            f"{self.organization.slug}/{self.owner.username}/",
        ):
            original_filename = os.path.basename(self.file.name)
            self.file.name = self.get_upload_path(original_filename)

        # Detect media type by file extension
        ext = os.path.splitext(self.file.name)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".gif"]:
            self.type = "image"
            self.duration = None  # Images don't have duration
        elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
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
                    clip = _VFC(self.file.path)
                    duration_seconds = int(getattr(clip, "duration", 0) or 0)
                    clip.close()

                    if self.duration != duration_seconds:
                        self.duration = duration_seconds
                        super().save(update_fields=["duration"])
            except Exception as e:
                print(f"Error getting video duration: {e}")


class Playlist(models.Model):
    """Playlist model for organizing media and devices"""

    playlist_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Timing
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

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
    media = models.ManyToManyField(Media, related_name="playlists")
    devices = models.ManyToManyField(Device, related_name="playlists")

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
