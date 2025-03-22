from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django import forms
from .models import User, Organization

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['expiration_date'].required = True
        self.fields['organization_db_name'].disabled = True  # set to readonly
        self.fields['organization_db_name'].widget.attrs['style'] = 'background-color: #f0f0f0;'

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make organization required
        self.fields['organization'].required = True


class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    list_display = ('id', 'clickable_username', 'is_superuser', 'get_organization_db_name', 'get_organization_name', 'device_limit', 'expiration_date')
    search_fields = ('username',)
    list_filter = ('is_superuser', 'organization')
    ordering = ('username',)
    readonly_fields = ('date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('organization', 'device_limit', 'expiration_date')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'organization', 'device_limit', 'expiration_date')
        }),
    )

    def clickable_username(self, obj):
        return format_html('<a href="{}">{}</a>', f"/admin/core/user/{obj.id}/change/", obj.username)
    clickable_username.allow_tags = True
    clickable_username.short_description = "Username"

    def get_organization_db_name(self, obj):
        return obj.organization.db_name if obj.organization else "-"
    get_organization_db_name.short_description = "Organization DB Name"

    def get_organization_name(self, obj):
        return obj.organization.name if obj.organization else "-"
    get_organization_name.short_description = "Organization Name"

admin.site.register(User, CustomUserAdmin)

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'clickable_name', 'db_name')
    search_fields = ('name', 'db_name')

    def clickable_name(self, obj):
        return format_html('<a href="{}">{}</a>', f"/admin/core/organization/{obj.id}/change/", obj.name)
    clickable_name.allow_tags = True
    clickable_name.short_description = "Organization Name"

    list_display = ('id', 'clickable_name', 'db_name')
    search_fields = ('name', 'db_name')

    def clickable_name(self, obj):
        return format_html('<a href="{}">{}</a>', f"/admin/core/organization/{obj.id}/change/", obj.name)
    clickable_name.allow_tags = True
    clickable_name.short_description = "Organization Name"