from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from organizations.models import Device, Media, Playlist
from core.models import User

from django.utils import timezone


class DeviceSerializer(serializers.ModelSerializer):
    sn = serializers.CharField(source='serial_number', required=True)

    class Meta:
        model = Device
        fields = ['device_id', 'sn', 'owner']
        extra_kwargs = {
            'owner': {'read_only': True}
        }

    def validate(self, attrs):
        username = self.initial_data.get("username")  # Get username from request data
        if not username:
            raise ValidationError(
                {"error": {"code": "MISSING_USERNAME", "message": "Username is required"}}
            )

        user = User.objects.filter(username__iexact=username).first()
        if not user:
            raise ValidationError(
                {"error": {"code": "USER_NOT_FOUND", "message": "User not found"}}
            )

        if user.expiration_date and user.expiration_date < timezone.localtime(timezone.now()).date():
            raise ValidationError(
                {"error": {"code": "EXPIRED_ACCOUNT", "message": "User's account has expired"}}
            )

        attrs['owner'] = user  # Assign user to owner field
        return attrs

    def to_internal_value(self, data):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError(
                {"error": {"code": "MISSING_CONTEXT", "message": "Request context is missing"}}
            )

        if "sn" not in data:
            raise serializers.ValidationError(
                {"error": {"code": "MISSING_SN", "message": "Serial number is required"}}
            )

        if Device.objects.filter(serial_number=data['sn']).exists():
            raise serializers.ValidationError(
                {"error": {"code": "DUPLICATE_SN", "message": "Device with this serial number already exists"}}
            )

        return super().to_internal_value(data)

    def validate_serial_number(self, value):
        if Device.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError(
                {"error": {"code": "DUPLICATE_SN", "message": "Device with this serial number already exists"}}
            )
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
