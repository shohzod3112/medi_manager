import hashlib

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from attachment.models import Attachment
from .forms import AttachmentForm, PlaylistAdminForm, OrganizationAdminForm

from .models import Device, DeviceType, File, Organization, Playlist, IoTDevice

User = get_user_model()

@admin.register(IoTDevice)
class IoTDeviceAdmin(admin.ModelAdmin):
    list_display = ('id',)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Organization model.
    """

    form = OrganizationAdminForm
    list_display = (
        "name",
        "is_active",
        "device_limit",
        "current_device_count",
        "expiration_date",
    )
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "current_device_count",
        "next_device_id",
    )

    # Note: The `fields` attribute is mutually exclusive with `fieldsets`.
    # We use `fieldsets` here for a better-structured admin page, which resolves (admin.E005).
    fieldsets = (
        ("General Information", {"fields": ("name", "description")}),
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
                "fields": ("created_by", "updated_by", "created_at", "updated_at"),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Automatically set the creator of the organization to the current user upon creation.
        """
        if change:
            obj.updated_by = request.user

        else:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    # form = DeviceAdminForm
    list_display = (
        'id',
        "organization_device_id",
        "name",
        "serial_number",
        "organization",
        "device_type",
        "is_active",
        "last_seen",
    )
    # Dinamik list_display
    def get_list_display(self, request):
        user = request.user

        if user.is_superuser:
            # Superuser hamma maydonlarni ko‘rsin
            return self.list_display
        elif user.role == "admin":
            # Manager uchun ayrim maydonlar
            return (
                "organization_device_id",
                "name",
                "serial_number",
                "device_type",
                "is_active",
            )
        return ("id",)
    list_filter = ("is_active", "device_type", "organization", "created_at")
    def get_list_filter(self, request):
        user = request.user
        if user.is_superuser:
            return self.list_filter
        elif user.role == "admin":
            return (
                "is_active",
                "device_type",
                "serial_number",
                "created_at"
            )
        return ("is_active",)

    search_fields = ("name", "serial_number", "organization__name")
    def get_search_fields(self, request):
        user = request.user
        if user.is_superuser:
            return self.search_fields
        elif user.role == "admin":
            return (
                "name", "serial_number"
            )
        return ("name",)

    readonly_fields = (
        "organization_device_id",
        "token",
        "serial_number",
        "last_seen",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    def get_readonly_fields(self, request, obj=None):
        user = request.user
        if user.role == "admin":
            return (
                "organization_device_id",
                "token",
                "serial_number",
                "last_seen",
            )
        return self.readonly_fields

    ordering = ("organization_device_id",)

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
        ("Security", {"fields": ("exit_password", "token")}),
        ("Status", {"fields": ("is_active", "last_seen")}),
    )

    def get_fieldsets(self, request, obj=None):
        user = request.user
        if user.is_superuser:
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
                ("Organization & User", {"fields": ("organization",)}),
                ("Security", {"fields": ("exit_password", "token")}),
                ("Status", {"fields": ("is_active", "last_seen")}),
                (
                    "Timestamps",
                    {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)},
                ),
            )
            return fieldsets
        return self.fieldsets

    def save_model(self, request, obj, form, change):
        if change:
            # UPDATE bo‘layapti
            raw_token = f"{request.user.username}-{obj.serial_number}"
            obj.token = hashlib.sha256(raw_token.encode()).hexdigest()
            obj.updated_by = request.user
        else:
            # CREATE bo‘layapti
            if obj.organization.has_reached_device_limit():
                raise ValidationError("Device soni limitdan oshib ketti!")
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related("organization", "device_type")
        )

        # Superuser hamma narsani ko‘ra oladi
        if request.user.is_superuser:
            return qs

        # Oddiy user faqat o'zining organizationidagi Device-larni ko'radi
        return qs.filter(organization=request.user.organization)


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "description",
        "device_count",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)
    readonly_fields = ("device_count", "created_at", "updated_at", "created_by", "updated_by")

    fieldsets = (
        (
            "Device Type Information",
            {
                "fields": (
                    "name",
                    "organization",
                    "description",
                    "is_active",
                ),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)},
        ),
    )

    def device_count(self, obj):
        return obj.devices.count()

    device_count.short_description = "Devices"

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    form = AttachmentForm
    list_display = ("id", "file_name", "file_type")

    fieldsets = (
        ("File Upload", {"fields": ("file", "file_name", "file_type")}),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if obj:
            # Eski File ni to'ldiramiz
            file_obj = File.objects.filter(attachment=obj).first()
            if file_obj:
                form.base_fields["file_name"].initial = file_obj.name
                form.base_fields["file_type"].initial = file_obj.type

        return form

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user

        # Attachmentni saqlaymiz
        super().save_model(request, obj, form, change)

        # File obyektini yaratamiz yoki yangilaymiz
        # FILE update/create
        if change:
            file_obj = File.objects.filter(attachment=obj).first()

            if file_obj:  # mavjud bo'lsa
                file_obj.name = form.cleaned_data["file_name"]
                file_obj.organization = request.user.organization
                file_obj.updated_by = request.user
                file_obj.save()
            else:
                # agar yo'q boʻlsa, yangisi yaratiladi
                File.objects.create(
                    attachment=obj,
                    name=form.cleaned_data["file_name"],
                    organization=request.user.organization,
                    created_by=request.user,
                    owner=request.user,
                )
        else:
            file_obj = File.objects.create(
                attachment=obj,
                name=form.cleaned_data["file_name"],
                owner=request.user,
                organization=request.user.organization,
                created_by=request.user,
            )

    # --- Custom columns ---
    def file_name(self, obj):
        file = File.objects.filter(attachment=obj).first()
        return file.name if file else "-"

    def file_type(self, obj):
        file = File.objects.filter(attachment=obj).first()
        return file.type if file else "-"


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    form = PlaylistAdminForm
    list_display = (
        "playlist_id", "name", "organization", "owner",
        "start_time", "end_time", "is_active",
        "file_count", "device_count",
    )
    def get_list_display(self, request):
        user = request.user
        if user.role == "admin":
            return (
                "playlist_id", "name",
                "start_time", "end_time", "is_active",
                "file_count", "device_count",
            )
        return self.list_display

    list_filter = ("is_active", "organization", "created_at")
    def get_list_filter(self, request):
        user = request.user
        if user.role == "admin":
            return (
                "is_active",
                "created_at"
            )
        return self.list_filter

    search_fields = ("name", "organization__name")
    def get_search_fields(self, request):
        user = request.user
        if user.role == "admin":
            return (
                "name",
            )
        return self.search_fields

    readonly_fields = ("playlist_id", "created_at", "updated_at", "created_by", "updated_by")
    ordering = ("-created_at",)

    fieldsets = (
        ("Playlist Information", {"fields": ("name", "description")}),
        ("Timing", {"fields": ("playlist_type", "start_date", "end_date","start_time", "end_time")}),
        ("Content", {"fields": ("file", "devices")}),
        ("Status", {"fields": ("is_active",)}),
        ("Organization & Owner", {"fields": ("organization", "owner")}),
        ("Timestamps",
         {"fields": ("created_at", "updated_at", "created_by", "updated_by"),
          "classes": ("collapse",)}
         ),
    )

    def get_fieldsets(self, request, obj=None):
        user = request.user
        if user.role == "admin":
            return (
                ("Playlist Information", {"fields": ("name", "description")}),
                ("Timing", {"fields": ("playlist_type", "start_date", "end_date","start_time", "end_time")}),
                ("Content", {"fields": ("file", "devices")}),
                ("Status", {"fields": ("is_active",)}),
                ("Timestamps",
                 {"fields": ("created_at", "updated_at", "created_by", "updated_by"),
                  "classes": ("collapse",)}
                 ),
            )
        return self.fieldsets

    # 🔥 CURRENT USER ni FORM ga uzatish
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        # wrap qilamiz va custom __init__ ga user beramiz
        class WrappedForm(form_class):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs["current_user"] = request.user
                super(WrappedForm, self2).__init__(*args, **inner_kwargs)

        return WrappedForm

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
            obj.owner = request.user
            if request.user.organization:
                obj.organization = request.user.organization
            else:
                raise ValidationError("Sizga organization biriktirilmagan")

        super().save_model(request, obj, form, change)

    def file_count(self, obj):
        return obj.file.count()

    file_count.short_description = "File"

    def device_count(self, obj):
        return obj.devices.count()

    device_count.short_description = "Devices"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("organization", "owner")


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    readonly_fields = ("organization_device_id", "token", "last_seen")
    fields = (
        "organization_device_id",
        "name",
        "serial_number",
        "is_active",
    )


# Add inlines to Organization admin
OrganizationAdmin.inlines = [DeviceInline]
