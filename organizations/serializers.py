from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from organizations.models import Device, Media, Playlist
from core.models import User


class DeviceSerializer(serializers.ModelSerializer):
    sn = serializers.CharField(source='serial_number', required=True)

    class Meta:
        model = Device
        fields = ['device_id', 'sn']

    def to_internal_value(self, data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is missing")

        if "sn" not in data:
            raise serializers.ValidationError({"sn": "This field is required."})

        if Device.objects.filter(serial_number=data['sn']).exists():
            raise serializers.ValidationError({"sn": "Device with this serial number already exists."})

        username = data.get("username")
        if not username:
            raise serializers.ValidationError({"username": "This field is required"})

        user = User.objects.filter(username__iexact=username).first()
        if not user:
            raise serializers.ValidationError({"username": "User not found"})

        validated_data = super().to_internal_value(data)
        validated_data['owner'] = user
        return validated_data

    def validate_serial_number(self, value):
        if Device.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError("Device with this serial number already exists.")
        return value


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ['media_id', 'name', 'type', 'file', 'duration', 'owner']


class PlaylistSerializer(serializers.ModelSerializer):
    media = serializers.PrimaryKeyRelatedField(many=True, queryset=Media.objects.all())  # Include media
    devices = serializers.PrimaryKeyRelatedField(many=True, queryset=Device.objects.all())  # Include devices

    class Meta:
        model = Playlist
        fields = ['playlist_id', 'name', 'owner', 'start_time', 'end_time', 'media', 'devices']
        read_only_fields = ['owner']
