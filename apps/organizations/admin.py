from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.utils.html import format_html

from apps.users.models import UserProfile

from .models import Device, DeviceType, File, Organization, Playlist

User = get_user_model()


class OrganizationAdminForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            "name",
            "slug",
            "description",
            "device_limit",
            "is_active",
            "expiration_date",
        ]

    def clean(self):
        cleaned_data = super().clean()
        device_limit = cleaned_data.get("device_limit")

        if device_limit and self.instance.pk:
            # Check if reducing device limit would affect existing users
            total_used = self.instance.get_total_used_devices()
            if device_limit < total_used:
                raise ValidationError(
                    f"Cannot reduce device limit to {device_limit}. "
                    f"Organization currently has {total_used} devices in use.",
                )

        return cleaned_data


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Organization model.
    """

    form = OrganizationAdminForm
    list_display = (
        "name",
        "slug",
        "is_active",
        "device_limit",
        "current_device_count",
        "expiration_date",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "current_device_count",
        "next_device_id",
    )

    # Note: The `fields` attribute is mutually exclusive with `fieldsets`.
    # We use `fieldsets` here for a better-structured admin page, which resolves (admin.E005).
    fieldsets = (
        ("General Information", {"fields": ("name", "slug", "description")}),
        (
            "Subscription Details",
            {"fields": ("device_limit", "expiration_date", "is_active")},
        ),
        # Each fieldset's second element must be a dictionary with a 'fields' key, which resolves (admin.E011).
        ("Usage Statistics", {"fields": ("current_device_count", "next_device_id")}),
        (
            "Audit Information",
            {
                "classes": ("collapse",),
                "fields": ("created_by", "created_at", "updated_at"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Automatically set the creator of the organization to the current user upon creation.
        """
        if not obj.pk:  # If the object is being created
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class DeviceAdminForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        user_profile = cleaned_data.get("user_profile")
        organization = cleaned_data.get("organization")

        if user_profile and organization:
            if user_profile.organization != organization:
                raise ValidationError(
                    "User profile must belong to the same organization as the device.",
                )

        return cleaned_data


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    form = DeviceAdminForm
    list_display = (
        'id',
        "organization_device_id",
        "full_device_id",
        "name",
        "serial_number",
        "organization",
        "user_profile",
        "device_type",
        "is_active",
        "last_seen",
    )
    list_filter = ("is_active", "device_type", "organization", "created_at")
    search_fields = ("name", "serial_number", "organization__name")
    readonly_fields = (
        "organization_device_id",
        "token",
        "last_seen",
        "created_at",
        "updated_at",
    )
    ordering = ("organization", "organization_device_id")

    fieldsets = (
        (
            "Device Information",
            {
                "fields": (
                    "organization_device_id",
                    "name",
                    "serial_number",
                    "device_type",
                ),
            },
        ),
        ("Organization & User", {"fields": ("organization", "user_profile")}),
        ("Security", {"fields": ("exit_password", "token")}),
        ("Status", {"fields": ("is_active", "last_seen")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def full_device_id(self, obj):
        return obj.get_full_device_id()

    full_device_id.short_description = "Full Device ID"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("organization", "user_profile__user", "device_type")
        )


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        "device_count",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("device_count", "created_at")

    def device_count(self, obj):
        return obj.devices.count()

    device_count.short_description = "Devices"


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        "file_id",
        "local_id",
        "name",
        "type",
        "organization",
        "owner",
        "duration",
        "created_at",
    )
    list_filter = ("type", "organization", "created_at")
    search_fields = ("name", "organization__name")
    readonly_fields = ("file_id", "duration", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("File Information", {"fields": ("name", "type", "file", "duration")}),
        ("Organization & Owner", {"fields": ("organization", "owner")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("organization", "owner")


# Playlist Admin
class PlaylistAdminForm(forms.ModelForm):
    file = forms.ModelMultipleChoiceField(
        queryset=File.objects.none(),
        widget=admin.widgets.FilteredSelectMultiple("File", is_stacked=False),
        required=False,
    )
    devices = forms.ModelMultipleChoiceField(
        queryset=Device.objects.none(),
        widget=admin.widgets.FilteredSelectMultiple("Devices", is_stacked=False),
        required=False,
    )

    class Meta:
        model = Playlist
        fields = "__all__"

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)

        # Filter choices based on ownership and device naming
        if self.current_user and not self.current_user.is_superuser:
            self.fields["file"].queryset = File.objects.filter(
                owner=self.current_user,
            )
            self.fields["devices"].queryset = (
                Device.objects.filter(user_profile__user=self.current_user)
                .exclude(name__isnull=True)
                .exclude(name__exact="")
            )
        else:
            self.fields["file"].queryset = File.objects.all()
            self.fields["devices"].queryset = Device.objects.exclude(
                name__isnull=True,
            ).exclude(name__exact="")

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.file.set(self.cleaned_data["file"])
            instance.devices.set(self.cleaned_data["devices"])
            self.save_m2m()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        # Only enforce on existing records
        if self.instance.pk:
            if not cleaned_data.get("file"):
                raise ValidationError({"file": "At least one file is required."})
            if not cleaned_data.get("devices"):
                raise ValidationError({"devices": "At least one device is required."})
        return cleaned_data


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    form = PlaylistAdminForm
    list_display = (
        "playlist_id",
        "name",
        "organization",
        "owner",
        "start_time",
        "end_time",
        "is_active",
        "file_count",
        "device_count",
    )
    list_filter = ("is_active", "organization", "created_at")
    search_fields = ("name", "organization__name")
    readonly_fields = ("playlist_id", "created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Playlist Information", {"fields": ("name", "description")}),
        ("Organization & Owner", {"fields": ("organization", "owner")}),
        ("Timing", {"fields": ("playlist_type", "start_date", "end_date","start_time", "end_time")}),
        ("Content", {"fields": ("file", "devices")}),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def file_count(self, obj):
        return obj.file.count()

    file_count.short_description = "File"

    def device_count(self, obj):
        return obj.devices.count()

    device_count.short_description = "Devices"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("organization", "owner")


# Inline admin for better organization management
class UserProfileInline(admin.TabularInline):
    model = UserProfile
    extra = 0
    readonly_fields = ("created_at",)
    fields = (
        "user",
        # "device_limit",
        "current_device_count",
        "is_active",
        "expiration_date",
    )


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    readonly_fields = ("organization_device_id", "token", "last_seen")
    fields = (
        "organization_device_id",
        "name",
        "serial_number",
        "user_profile",
        "is_active",
    )


# Add inlines to Organization admin
OrganizationAdmin.inlines = [UserProfileInline, DeviceInline]
