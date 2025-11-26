from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Attachment, File, Device, Playlist, Organization


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


class AttachmentForm(forms.ModelForm):
    file_name = forms.CharField(label="File Name", required=False)
    file_type = forms.CharField(label="Type", required=False, disabled=True)

    class Meta:
        model = Attachment
        fields = ["file"]      # Faqat file ko‘rinadi, name yo‘q

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