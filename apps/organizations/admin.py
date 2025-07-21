from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings
from django.db.models import Count, Sum

from .models import Organization, Device, Media, Playlist, DeviceType
from user.models import UserProfile

User = get_user_model()


class OrganizationAdminForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        device_limit = cleaned_data.get('device_limit')
        
        if device_limit and self.instance.pk:
            # Check if reducing device limit would affect existing users
            total_used = self.instance.get_total_used_devices()
            if device_limit < total_used:
                raise ValidationError(
                    f'Cannot reduce device limit to {device_limit}. '
                    f'Organization currently has {total_used} devices in use.'
                )
        
        return cleaned_data


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationAdminForm
    list_display = (
        'id', 'name', 'slug', 'device_limit', 'used_devices', 'available_slots', 
        'user_count', 'is_active', 'expiration_status'
    )
    list_filter = ('is_active', 'expiration_date', 'created_at')
    search_fields = ('name', 'slug', 'db_name')
    ordering = ('name',)
    readonly_fields = ('used_devices', 'available_slots', 'user_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Device Management', {
            'fields': ('device_limit', 'used_devices', 'available_slots', 'next_device_id')
        }),
        ('Organization Settings', {
            'fields': ('is_active', 'expiration_date')
        }),
        ('Database Configuration', {
            'fields': ('db_name',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def used_devices(self, obj):
        return obj.get_total_used_devices()
    used_devices.short_description = "Used Devices"

    def available_slots(self, obj):
        return obj.get_available_device_slots()
    available_slots.short_description = "Available Slots"

    def user_count(self, obj):
        return obj.get_user_count()
    user_count.short_description = "Users"

    def expiration_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.expiration_date:
            return format_html('<span style="color: orange;">Active</span>')
        else:
            return format_html('<span style="color: green;">No Expiration</span>')
    expiration_status.short_description = "Status"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            user_count=Count('user_profiles'),
            used_devices=Sum('user_profiles__current_device_count')
        )


class DeviceAdminForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        user_profile = cleaned_data.get('user_profile')
        organization = cleaned_data.get('organization')
        
        if user_profile and organization:
            if user_profile.organization != organization:
                raise ValidationError(
                    'User profile must belong to the same organization as the device.'
                )
        
        return cleaned_data


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    form = DeviceAdminForm
    list_display = (
        'organization_device_id', 'full_device_id', 'name', 'serial_number', 
        'organization', 'user_profile', 'device_type', 'is_active', 'last_seen'
    )
    list_filter = ('is_active', 'device_type', 'organization', 'created_at')
    search_fields = ('name', 'serial_number', 'organization__name', 'user_profile__user__username')
    readonly_fields = ('organization_device_id', 'token', 'last_seen', 'created_at', 'updated_at')
    ordering = ('organization', 'organization_device_id')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('organization_device_id', 'name', 'serial_number', 'device_type')
        }),
        ('Organization & User', {
            'fields': ('organization', 'user_profile')
        }),
        ('Security', {
            'fields': ('exit_password', 'token')
        }),
        ('Status', {
            'fields': ('is_active', 'last_seen')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def full_device_id(self, obj):
        return obj.get_full_device_id()
    full_device_id.short_description = "Full Device ID"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'user_profile__user', 'device_type'
        )


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'device_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('device_count', 'created_at')

    def device_count(self, obj):
        return obj.devices.count()
    device_count.short_description = "Devices"


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('media_id', 'name', 'type', 'organization', 'owner', 'duration', 'created_at')
    list_filter = ('type', 'organization', 'created_at')
    search_fields = ('name', 'organization__name', 'owner__username')
    readonly_fields = ('media_id', 'duration', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Media Information', {
            'fields': ('name', 'type', 'file', 'duration')
        }),
        ('Organization & Owner', {
            'fields': ('organization', 'owner')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'owner')


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        'playlist_id', 'name', 'organization', 'owner', 'start_time', 'end_time', 
        'is_active', 'media_count', 'device_count'
    )
    list_filter = ('is_active', 'organization', 'created_at')
    search_fields = ('name', 'organization__name', 'owner__username')
    readonly_fields = ('playlist_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('Playlist Information', {
            'fields': ('name', 'description')
        }),
        ('Organization & Owner', {
            'fields': ('organization', 'owner')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Content', {
            'fields': ('media', 'devices')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def media_count(self, obj):
        return obj.media.count()
    media_count.short_description = "Media"

    def device_count(self, obj):
        return obj.devices.count()
    device_count.short_description = "Devices"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'owner')


# Inline admin for better organization management
class UserProfileInline(admin.TabularInline):
    model = UserProfile
    extra = 0
    readonly_fields = ('current_device_count', 'created_at')
    fields = ('user', 'device_limit', 'current_device_count', 'is_active', 'expiration_date')


class DeviceInline(admin.TabularInline):
    model = Device
    extra = 0
    readonly_fields = ('organization_device_id', 'token', 'last_seen')
    fields = ('organization_device_id', 'name', 'serial_number', 'user_profile', 'is_active')


# Add inlines to Organization admin
OrganizationAdmin.inlines = [UserProfileInline, DeviceInline]
