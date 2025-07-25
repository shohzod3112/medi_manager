from drf_yasg import openapi
from drf_yasg.utils import swagger_serializer_method
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.utils import timezone

from apps.organizations.models import Device, Media, Playlist
from apps.users.models import User, UserProfile


class DeviceSerializer(serializers.ModelSerializer):
    sn = serializers.CharField(source='serial_number', required=True)
    username = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = Device
        fields = ['organization_id', 'sn', 'username']
        extra_kwargs = {
            'organization_id': {'required': False}
        }

    def create(self, validated_data):
        validated_data.pop('username', None)
        return Device.objects.create(**validated_data)

    def validate(self, attrs):
        username = self.initial_data.get("username")

        try:
            # Fetch user and their profile in one go to be efficient.
            user = User.objects.select_related('profile__organization').get(username__iexact=username)
            user_profile = user.profile
        except (User.DoesNotExist, User.profile.RelatedObjectDoesNotExist):
            # Raise an error that the view can handle.
            raise ValidationError("User not found")

        # Check if the user's account is expired via the profile.
        if user_profile.is_expired():
            raise ValidationError("User's account has expired")

        # Add the related objects to the validated data.
        # These will be passed to the `create` method.
        attrs['user_profile'] = user_profile
        attrs['organization'] = user_profile.organization

        return attrs

    def validate_serial_number(self, value):
        if Device.objects.filter(serial_number=value).exists():
            # Raise error with a simple string to be compatible with the view's error handling.
            raise serializers.ValidationError("Device with this serial number already exists")
        return value

    @swagger_serializer_method(serializer_or_field=openapi.Schema(
        type=openapi.TYPE_STRING,
        description="Username of the owner of the device"
    ))
    def get_username(self, obj):
        # This method is used for GET requests and was pointing to a non-existent 'owner' field.
        if obj.user_profile and obj.user_profile.user:
            return obj.user_profile.user.username
        return None


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
