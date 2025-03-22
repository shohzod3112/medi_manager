from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from organizations.models import Device, Media, Playlist
from core.models import User


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['device_id', 'serial_number']

    def validate(self, attrs):
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("Request context is missing")

        username = request.data.get("username")
        if not username:
            raise serializers.ValidationError({"username": "This field is required"})

        user = User.objects.filter(username__iexact=username).first()
        if not user:
            raise ValidationError({"username": "User not found"})

        attrs['owner'] = user
        return attrs

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
