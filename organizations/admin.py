from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.html import format_html
from django.conf import settings

from .models import Device, Media, Playlist, DeviceType

User = get_user_model()

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


@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_owners')
    list_display_links = ("id", "name")
    ordering = ('id',)
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


class DeviceAdminForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        owner = self.instance.owner

        if owner:
            user = User.objects.get(pk=owner.pk)
            if user.device_limit <= user.devices.count():
                raise ValidationError('Device limit exceeded.')

        return cleaned_data


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    form = DeviceAdminForm
    list_display = (
        'device_id', 'name', 'device_type', 'owner', 'serial_number',
        'exit_password', 'last_seen', 'media_preview'
    )
    list_display_links = ('device_id', 'name')
    search_fields = ('name', 'serial_number', 'device_type__name', 'owner__username')
    readonly_fields = ('serial_number', 'last_seen', 'owner', 'token')
    ordering = ('device_id',)

    def media_preview(self, obj):
        media_qs = Media.objects.filter(
            playlist__devices=obj,
            playlist__owner=obj.owner
        ).distinct().order_by('media_id')

        if not media_qs.exists():
            return "-"

        media = media_qs.first()
        if media.type == "image":
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px;" />',
                media.file.url)
        elif media.type == "video":
            preview_url = f"{settings.MEDIA_URL}previews/media_{media.media_id}.jpg"
            return format_html(
                '<img src="{}" style="width: 100px; height: 100px;" />',
                preview_url
            )
        return "-"

    media_preview.short_description = 'Media Preview'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('media_id', 'name', 'type', 'owner_display', 'duration')
    list_display_links = ("media_id", "name")
    search_fields = ('name', 'owner__username')
    list_filter = ('type', 'name')
    readonly_fields = ('owner', 'duration')
    ordering = ('media_id',)

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def owner_display(self, obj):
        return obj.owner.username
    owner_display.short_description = 'Owner'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)


# Playlist Admin
class PlaylistAdminForm(forms.ModelForm):
    media = forms.ModelMultipleChoiceField(
        queryset=Media.objects.none(),
        widget=admin.widgets.FilteredSelectMultiple('Media', is_stacked=False),
        required=False
    )
    devices = forms.ModelMultipleChoiceField(
        queryset=Device.objects.none(),
        widget=admin.widgets.FilteredSelectMultiple('Devices', is_stacked=False),
        required=False
    )

    class Meta:
        model = Playlist
        fields = '__all__'

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)

        # Filter choices based on ownership and device naming
        if self.current_user and not self.current_user.is_superuser:
            self.fields['media'].queryset = Media.objects.filter(owner=self.current_user)
            self.fields['devices'].queryset = (
                Device.objects.filter(owner=self.current_user)
                         .exclude(name__isnull=True)
                         .exclude(name__exact='')
            )
        else:
            self.fields['media'].queryset = Media.objects.all()
            self.fields['devices'].queryset = Device.objects.exclude(name__isnull=True).exclude(name__exact='')

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            instance.media.set(self.cleaned_data['media'])
            instance.devices.set(self.cleaned_data['devices'])
            self.save_m2m()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        # Only enforce on existing records
        if self.instance.pk:
            if not cleaned_data.get('media'):
                raise ValidationError({'media': 'At least one media file is required.'})
            if not cleaned_data.get('devices'):
                raise ValidationError({'devices': 'At least one device is required.'})
        return cleaned_data

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    form = PlaylistAdminForm
    list_display = (
        'playlist_id', 'name', 'formatted_start_time', 'formatted_end_time',
        'owner', 'display_media', 'display_devices'
    )
    list_display_links = ('playlist_id', 'name')
    list_filter = ('name',)
    search_fields = ('name', 'owner__username',)
    readonly_fields = ('owner',)
    ordering = ('playlist_id',)

    def get_form(self, request, obj=None, **kwargs):
        FormClass = super().get_form(request, obj, **kwargs)
        class WrappedForm(FormClass):
            def __init__(self, *args, **inner_kwargs):
                inner_kwargs['current_user'] = request.user
                super().__init__(*args, **inner_kwargs)
        return WrappedForm

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'media':
            kwargs['queryset'] = Media.objects.filter(owner=request.user)
        if db_field.name == 'devices':
            kwargs['queryset'] = (
                Device.objects.filter(owner=request.user)
                      .exclude(name__isnull=True)
                      .exclude(name__exact='')
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def formatted_start_time(self, obj):
        return timezone.localtime(obj.start_time).strftime('%Y-%m-%d %H:%M:%S')
    formatted_start_time.short_description = 'Start Time'

    def formatted_end_time(self, obj):
        return timezone.localtime(obj.end_time).strftime('%Y-%m-%d %H:%M:%S')
    formatted_end_time.short_description = 'End Time'

    def display_media(self, obj):
        names = [m.name for m in obj.media.all() if m.name]
        return ", ".join(names) if names else '-'
    display_media.short_description = 'Media'

    def display_devices(self, obj):
        names = [d.name for d in obj.devices.all() if d.name]
        return ", ".join(names) if names else '-'
    display_devices.short_description = 'Devices'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs if request.user.is_superuser else qs.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        super().save_model(request, obj, form, change)
