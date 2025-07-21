from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django import forms
from django.contrib.auth.forms import UserChangeForm

from user.models import User, UserProfile


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    list_display = ('id', 'clickable_username', 'email', 'full_name', 'is_active', 'date_joined', 'organization_info')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    ordering = ('id',)
    readonly_fields = ('date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')
        }),
    )

    def clickable_username(self, obj):
        return format_html('<a href="{}">{}</a>', f"/admin/user/user/{obj.id}/change/", obj.username)
    clickable_username.allow_tags = True
    clickable_username.short_description = "Username"

    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = "Full Name"

    def organization_info(self, obj):
        try:
            profile = obj.profile
            return format_html(
                '<span style="color: green;">{}</span> ({} devices)',
                profile.organization.name,
                profile.current_device_count
            )
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: red;">No Organization</span>')
    organization_info.short_description = "Organization"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'organization', 'device_limit', 'current_device_count', 'remaining_devices', 'is_active', 'expiration_status')
    list_filter = ('is_active', 'organization', 'expiration_date')
    search_fields = ('user__username', 'user__email', 'organization__name')
    ordering = ('organization', 'user__username')
    readonly_fields = ('current_device_count', 'created_at', 'updated_at')

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'organization')
        }),
        ('Device Management', {
            'fields': ('device_limit', 'current_device_count')
        }),
        ('Status', {
            'fields': ('is_active', 'expiration_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def remaining_devices(self, obj):
        return obj.get_remaining_devices()
    remaining_devices.short_description = "Remaining Devices"

    def expiration_status(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.expiration_date:
            return format_html('<span style="color: orange;">Active</span>')
        else:
            return format_html('<span style="color: green;">No Expiration</span>')
    expiration_status.short_description = "Expiration Status"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'organization')