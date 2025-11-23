import hashlib

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.html import format_html
from attachment.models import Attachment

from .models import Device, DeviceType, File, Organization, Playlist

User = get_user_model()


class OrganizationAdminForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            "name",
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
            obj.created_by = request.user
            if obj.expiration_date < timezone.now().date():
                obj.is_active = False
            else:
                obj.is_active = True

        if not obj.pk:  # If the object is being created
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# class DeviceAdminForm(forms.ModelForm):
#     class Meta:
#         model = Device
#         fields = "__all__"
#
#     def clean(self):
#         cleaned_data = super().clean()
#         user_profile = cleaned_data.get("user_profile")
#         organization = cleaned_data.get("organization")
#
#         if user_profile and organization:
#             if user_profile.organization != organization:
#                 raise ValidationError(
#                     "User profile must belong to the same organization as the device.",
#                 )
#
#         return cleaned_data


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
    list_filter = ("is_active", "device_type", "organization", "created_at")
    search_fields = ("name", "serial_number", "organization__name")
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
        # ("Organization & User", {"fields": ("organization", "user_profile")}),
        ("Security", {"fields": ("exit_password", "token")}),
        ("Status", {"fields": ("is_active", "last_seen")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)},
        ),
    )

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


class FileInline(admin.StackedInline):
    model = File
    extra = 0
    max_num = 1
    can_delete = True
    fields = ("name", "type")
    readonly_fields = ('type',)

    # Faqat user.organization ga tegishli File-lar ko‘rsatiladi
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(organization=request.user.organization)

    # Bitta Attachmentga faqat 1 File
    def has_add_permission(self, request, obj):
        if obj and obj.files.exists():
            return False
        return True

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in instances:
            if obj.pk:
                obj.updated_by = request.user
            else:
                obj.created_by = request.user
                obj.owner = request.user
                obj.organization = request.user.organization

            obj.save()

        formset.save_m2m()


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "file_name", "file_type")
    inlines = [FileInline]

    fieldsets = (
        (
            "Attachment Information",
            {"fields": ("name","file")}
        ),
    )

    readonly_fields = (
        "file_name", "file_type", "name"
    )

    # Attachment ro‘yxati ham user.organization bo‘yicha cheklanadi
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.is_superuser:
            return qs

        return qs.filter(files__organization=request.user.organization).distinct()

    # INLINE orqali yaratilgan File-ga owner & organization berish
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        for obj in instances:
            if isinstance(obj, File):
                if not obj.owner_id:
                    obj.owner = request.user
                if not obj.organization_id:
                    obj.organization = request.user.organization
            obj.save()

        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        if change:
            obj.updated_by = request.user
        else:
            obj.name = obj.file.name.split("/")[-1]
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # --- Custom READONLY fields ---

    def file_name(self, obj):
        try:
            file_obj = File.objects.get(attachment=obj)
        except File.DoesNotExist:
            return "-"
        return file_obj.name

    file_name.short_description = "File Name"

    def file_type(self, obj):
        try:
            file_obj = File.objects.get(attachment=obj)
        except File.DoesNotExist:
            return "-"
        return file_obj.type

    file_type.short_description = "File Type"


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

        # FILELAR
        if self.current_user and not self.current_user.is_superuser:
            self.fields["file"].queryset = File.objects.filter(owner=self.current_user)
        else:
            self.fields["file"].queryset = File.objects.all()

        # DEVICELAR
        if self.current_user and not self.current_user.is_superuser:
            self.fields["devices"].queryset = (
                Device.objects.filter(organization=self.current_user.organization)
                .exclude(name__isnull=True)
                .exclude(name__exact="")
            )
        else:
            self.fields["devices"].queryset = (
                Device.objects.exclude(name__isnull=True)
                .exclude(name__exact="")
            )

    def clean(self):
        cleaned_data = super().clean()

        # faqat update payti majburiy
        if self.instance.pk:
            if not cleaned_data.get("file"):
                raise ValidationError({"file": "At least one file is required."})
            if not cleaned_data.get("devices"):
                raise ValidationError({"devices": "At least one device is required."})

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.file.set(self.cleaned_data["file"])
            instance.devices.set(self.cleaned_data["devices"])
        return instance


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    form = PlaylistAdminForm
    list_display = (
        "playlist_id", "name", "organization", "owner",
        "start_time", "end_time", "is_active",
        "file_count", "device_count",
    )
    list_filter = ("is_active", "organization", "created_at")
    search_fields = ("name", "organization__name")
    readonly_fields = ("playlist_id", "created_at", "updated_at", "created_by", "updated_by")
    ordering = ("-created_at",)

    fieldsets = (
        ("Playlist Information", {"fields": ("name", "description")}),
        ("Timing", {"fields": ("playlist_type", "start_date", "end_date","start_time", "end_time")}),
        ("Content", {"fields": ("file", "devices")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps",
         {"fields": ("created_at", "updated_at", "created_by", "updated_by"),
          "classes": ("collapse",)}
         ),
    )

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
