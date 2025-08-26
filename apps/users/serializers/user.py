from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "is_superuser")


class ProfileSerializer(serializers.Serializer):
    def to_representation(self, user: User):
        profile = getattr(user, "profile", None)
        org = getattr(profile, "organization", None) if profile else None
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
            },
            "organization": None
            if not org
            else {
                "id": getattr(org, "id", None),
                "name": getattr(org, "name", None),
                "slug": getattr(org, "slug", None),
                "device_limit": getattr(org, "device_limit", None),
                "current_device_count": org.get_total_used_devices() if org else None,
                "is_active": getattr(org, "is_active", None),
                "is_expired": org.is_expired() if org else None,
                "expiration_date": getattr(org, "expiration_date", None),
            },
            "profile": None
            if not profile
            else {
                "device_limit": profile.device_limit,
                "current_device_count": profile.current_device_count,
                "remaining_devices": profile.get_remaining_devices(),
                "is_active": profile.is_active,
                "is_expired": profile.is_expired(),
                "expiration_date": profile.expiration_date,
            },
        }
