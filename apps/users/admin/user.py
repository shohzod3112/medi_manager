from django import forms
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.html import format_html

from apps.users.models import User

# Ensure idempotent registration to avoid AlreadyRegistered during test discovery
try:
    admin.site.unregister(User)
except NotRegistered:
    pass


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    list_display = (
        "id",
        "role",
        "clickable_username",
        "email",
        "full_name",
        "is_active",
        "date_joined",
        "organization_info",
    )
    search_fields = ("username", "role", "email", "first_name", "last_name")
    list_filter = ("is_active", "is_staff", "is_superuser", "date_joined")
    ordering = ("id",)
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Personal Info",
            {"fields": ("role", "organization", "first_name", "last_name", "email", "phone_number", "avatar")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                ),
            },
        ),
    )

    def clickable_username(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f"/admin/users/user/{obj.id}/change/",
            obj.username,
        )

    clickable_username.allow_tags = True
    clickable_username.short_description = "Username"

    def full_name(self, obj):
        return obj.get_full_name()

    full_name.short_description = "Full Name"

    def organization_info(self, obj):
        if obj.organization:
            return format_html(
                '<span style="color: green;">{}</span>',
                obj.organization.name,
            )
        else:
            return format_html('<span style="color: red;">No Organization</span>')

    organization_info.short_description = "Organization"
