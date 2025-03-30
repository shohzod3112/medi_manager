from drf_yasg import openapi
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from organizations.models import Device, Media, Playlist
from core.models import User

from django.utils import timezone


class DeviceSerializer(serializers.ModelSerializer):
    sn = serializers.CharField(source='serial_number', required=True)
    username = serializers.CharField(write_only=True, required=True)


    class Meta:
        model = Device
        fields = ['device_id', 'sn', 'owner', 'username']
        extra_kwargs = {
            'owner': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data.pop('username', None)
        return Device.objects.create(**validated_data)

    def validate(self, attrs):
        username = self.initial_data.get("username")
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
        if 'username' in data:
            data['owner'] = data.get('username', None)

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

    @swagger_serializer_method(serializer_or_field=openapi.Schema(
        type=openapi.TYPE_STRING,
        description="Username of the owner of the device"
    ))
    def get_username(self, obj):
        return obj.owner.username if obj.owner else None



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
