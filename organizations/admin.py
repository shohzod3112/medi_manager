from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import models
from .models import Device, Media, Playlist, DeviceType, PlaylistMedia, PlaylistDevice

User = get_user_model()

# DeviceType Admin form with multiple selectable owners
class DeviceTypeAdminForm(forms.ModelForm):
    owners = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('owners', is_stacked=False),
        required=False
    )

    class Meta:
        model = DeviceType
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        if self.current_user and not self.current_user.is_superuser:
            self.fields['owners'].queryset = User.objects.filter(pk=self.current_user.pk)
        else:
            self.fields['owners'].queryset = User.objects.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.owners.set(self.cleaned_data['owners'])
            self.save_m2m()
        return instance

# DeviceType Admin with multiple owners
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_owners')
    form = DeviceTypeAdminForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        class FormWithRequest(form):
            def __new__(cls, *args, **kwargs):
                kwargs['current_user'] = request.user
                return form(*args, **kwargs)
        return FormWithRequest

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owners=request.user)

    def display_owners(self, obj):
        return ", ".join(user.username for user in obj.owners.all())
    display_owners.short_description = 'Owners'

admin.site.register(DeviceType, DeviceTypeAdmin)

# Device Admin
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'name', 'device_type', 'owner', 'serial_number', 'exit_password', 'last_seen')
    search_fields = ('name', 'serial_number', 'device_type__name', 'owner__username')
    readonly_fields = ('serial_number', 'last_seen', 'owner')
    # exclude = ("token",)


    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'device_type':
            kwargs["queryset"] = DeviceType.objects.filter(owners=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(Device, DeviceAdmin)

# Media Admin
@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('media_id', 'name', 'type', 'owner_display', 'duration')
    search_fields = ('name', 'owner__username')
    list_filter = ('type', 'owner')
    readonly_fields = ('owner',)

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def owner_display(self, obj):
        return obj.owner.username
    owner_display.short_description = 'Owner'

# PlaylistMedia Inline
class PlaylistMediaInline(admin.TabularInline):
    model = PlaylistMedia
    extra = 0
    min_num = 1

# PlaylistDevice Inline
class PlaylistDeviceInline(admin.TabularInline):
    model = PlaylistDevice
    extra = 0
    min_num = 1
    # raw_id_fields = ('device',)

# Playlist Admin Form
class PlaylistAdminForm(forms.ModelForm):
    class Meta:
        model = Playlist
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            return cleaned_data
        if not self.instance.media.exists():
            raise ValidationError({'media': 'At least one media file is required.'})
        if not self.instance.devices.exists():
            raise ValidationError({'devices': 'At least one device is required.'})
        return cleaned_data

# Playlist Admin
@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner',)
    list_filter = ('owner',)
    search_fields = ('name', 'owner__username',)
    readonly_fields = ('owner',)
    inlines = [PlaylistDeviceInline, PlaylistMediaInline]

    def get_queryset(self, request):
        """Ensure users only see their own playlists."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


    def save_model(self, request, obj, form, change):
        """Automatically set playlist owner to logged-in user."""
        # if not request.user.is_superuser:
        obj.owner = request.user
        super().save_model(request, obj, form, change)
