from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.organizations.models import Device, File, Organization, Playlist, DeviceType
from apps.users.models import UserProfile, User


class DeviceRetrieveSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    user_profile = serializers.SerializerMethodField()
    device_type = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = (
            "id", "organization_device_id", "name", "serial_number",
            "device_type", "exit_password", "token", "organization",
            "user_profile", "is_active", "last_seen", "created_at", "updated_at"
        )

    def get_device_type(self, obj):
        if obj.device_type:
            return {
                "id": obj.device_type.id,
                "name": obj.device_type.name,
            }

    def get_organization(self, obj):
        if obj.organization:
            return {
                "id": obj.organization.id,
                "name": obj.organization.name,
            }

    def get_user_profile(self, obj):
        if obj.user_profile:
            return {
                "id": obj.user_profile.id,
                "name": obj.user_profile.user.get_full_name(),
                "username": obj.user_profile.user.username,
            }


class FileSelectListSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ['value', 'label']

    def get_value(self, obj):
        return obj.file_id

    def get_label(self, obj):
        return obj.attachment.name

class DeviceSelectListSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ['value', 'label']

    def get_value(self, obj):
        return obj.id

    def get_label(self, obj):
        return obj.name


class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = "__all__"


class DeviceTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "created_at",
        ]

class DeviceTypeSelectListSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = DeviceType
        fields = ['value', 'label']

    def get_value(self, obj):
        return obj.id

    def get_label(self, obj):
        return obj.name


def ensure_default_org_profile(user):
    """Ensure the user has a profile and organization; create defaults if missing."""
    profile = getattr(user, "profile", None)
    if profile and profile.organization_id:
        return profile
    org, _ = Organization.objects.get_or_create(
        name="test_org",
        defaults={"description": "Auto provisioned"},
    )
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"organization": org},
    )
    if not profile.organization_id:
        profile.organization = org
        profile.save(update_fields=["organization"])
    return profile


class DeviceCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)

    class Meta:
        model = Device
        fields = [
            "id",
            "username",
            "serial_number",
            "name",
            "device_type",
            "is_active",
            "last_seen",
            "created_at",
        ]
        read_only_fields = ["id", "is_active", "last_seen", "created_at"]

    def create(self, validated_data):
        username = validated_data.pop("username")
        serial_number = validated_data.get("serial_number")

        # 🔍 Foydalanuvchini topamiz
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"username": "User not found"})

        # 🔍 UserProfile ni topamiz
        profile = getattr(user, "profile", None)
        if not profile:
            raise serializers.ValidationError({"username": "UserProfile not found"})

        # 🔍 Tashkilotni olamiz
        organization = profile.organization
        if not organization:
            raise serializers.ValidationError({"organization": "Organization not found"})

        # 📱 Device obyektini yaratamiz
        device = Device.objects.create(
            serial_number=serial_number,
            name=validated_data.get("name", ""),
            device_type=validated_data.get("device_type"),
            organization=organization,
            user_profile=profile,
        )
        return device

    def to_representation(self, instance):
        """Response formatini moslab chiqaramiz"""
        return {
            "id": instance.id,
            "organization": instance.organization.name,
            "organization_device_id": instance.organization_device_id,
            "name": instance.name,
            "serial_number": instance.serial_number,
            "device_type": instance.device_type.name if instance.device_type else None,
            "token": instance.token,
            "created_at": instance.created_at,
        }


class DeviceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'id',
            'name',
            'device_type',
            'exit_password',
        ]


class DeviceSerializer(serializers.ModelSerializer):
    device_type = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ["id", "serial_number", "name", "exit_password", "token", "device_type"]
        extra_kwargs = {
            "token": {"read_only": True},
            "serial_number": {
                "write_only": True,
                "required": True,
                "allow_blank": False,
            },
            "name": {"required": False},
            "exit_password": {"required": False},
            "device_type": {"required": True},
        }

    def get_device_type(self, obj):
        if obj.device_type:
            return {
                "id": obj.device_type.id,
                "name": obj.device_type.name,
            }

    def validate_serial_number(self, value):
        if Device.objects.filter(serial_number=value).exists():
            raise serializers.ValidationError(
                "Device with this serial number already exists",
            )
        return value

    def validate(self, attrs):
        org = attrs.get("organization")
        if org and org.has_reached_device_limit():
            raise serializers.ValidationError(
                {"organization": "Device soni limitdan oshib ketti"}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        profile = getattr(user, "profile", None)
        if not profile or not profile.organization_id:
            profile = ensure_default_org_profile(user)
        # Assign user and organization to the device
        validated_data["user_profile"] = profile
        validated_data["organization"] = profile.organization
        return super().create(validated_data)


class FileListSerializer(serializers.ModelSerializer):
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ["file_id", "name", "type", "attachment", "duration", "owner"]

    def get_attachment(self, obj):
        request = self.context.get("request")
        if obj.attachment:
            return {
                "id": obj.attachment.id,
                "name": obj.attachment.name,
                "file": request.build_absolute_uri(obj.attachment.file.url) if request else None,
            }


class FileSerializer(serializers.ModelSerializer):
    # file = serializers.FileField(required=False, allow_empty_file=True)

    class Meta:
        model = File
        fields = ["file_id", "name", "type", "attachment", "duration", "owner"]
        read_only_fields = ["owner", "duration", "type"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        profile = getattr(user, "profile", None)
        if not profile or not profile.organization_id:
            profile = ensure_default_org_profile(user)

        org = profile.organization
        validated_data["owner"] = user
        validated_data["organization"] = org

        # # If no file provided (legacy tests), generate a tiny dummy image file
        # if not validated_data.get("attachment"):
        #     dummy_content = ContentFile(b"dummy image content", name="placeholder.jpg")
        #     validated_data["file"] = dummy_content

        return super().create(validated_data)


class PlaylistSerializer(serializers.ModelSerializer):
    file = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=File.objects.all(),
        required=False,
    )
    devices = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Device.objects.all(),
        required=False,
    )

    class Meta:
        model = Playlist
        fields = [
            "playlist_id",
            "name",
            "owner",
            "playlist_type",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "file",
            "devices",
        ]
        read_only_fields = ["owner"]

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user
        profile = getattr(user, "profile", None)
        playlist_type = attrs.get("playlist_type")
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if playlist_type == "event":
            if not start_date or not end_date:
                raise ValidationError(
                    {"detail": "Tadbir turidagi playlist uchun start_date va end_date majburiy!"}
                )
            if end_date < start_date:
                raise ValidationError(
                    {"detail": "end_date start_date dan oldin bo'lishi mumkin emas!"}
                )
        if not profile or not profile.organization_id:
            profile = ensure_default_org_profile(user)

        org = profile.organization
        # Ensure all media and devices belong to the same organization
        files_list = attrs.get("file", []) or []
        devices_list = attrs.get("devices", []) or []
        if any(m.organization_id != org.id for m in files_list):
            raise serializers.ValidationError(
                {"files": "All files must belong to your organization"},
            )
        if any(d.organization_id != org.id for d in devices_list):
            raise serializers.ValidationError(
                {"devices": "All devices must belong to your organization"},
            )
        return attrs

    def create(self, validated_data):
        file = validated_data.pop("file", [])
        devices = validated_data.pop("devices", [])
        request = self.context.get("request")
        user = request.user
        profile = getattr(user, "profile", None)
        if not profile or not profile.organization_id:
            profile = ensure_default_org_profile(user)

        org = profile.organization
        playlist = Playlist.objects.create(
            owner=user,
            organization=org,
            **validated_data,
        )
        if file:
            playlist.file.set(file)
        if devices:
            playlist.devices.set(devices)
        return playlist


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "device_limit",
            "expiration_date",
            "is_active",
            "current_device_count",
            "next_device_id",
        ]
        read_only_fields = ["current_device_count", "next_device_id"]


class OrganizationSelectSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['value', 'label']

    def get_value(self, obj):
        return obj.id

    def get_label(self, obj):
        return obj.name
