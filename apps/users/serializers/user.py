from rest_framework import serializers

from apps.users.models import User, UserProfile


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
                # "device_limit": getattr(org, "device_limit", None),
                # "current_device_count": org.get_total_used_devices() if org else None,
                "is_active": getattr(org, "is_active", None),
                "is_expired": org.is_expired() if org else None,
                "expiration_date": getattr(org, "expiration_date", None),
            },
            "profile": None
            if not profile
            else {
                # "device_limit": profile.device_limit,
                # "current_device_count": profile.current_device_count,
                # "remaining_devices": profile.get_remaining_devices(),
                "is_active": profile.is_active,
                "is_expired": profile.is_expired(),
                "expiration_date": profile.expiration_date,
            },
        }


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "password",
            "password_confirm",
        ]

        extra_kwargs = {
            "email": {"required": True},
            "username": {"required": True},
        }

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError("Passwords must match!")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")  # kerak emas
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)  # parolni xeshlab saqlash
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "is_active",
            "date_joined",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url)


class UserRetrieveSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "avatar",
            "last_login",
            "is_superuser",
            "is_staff",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
            "phone_number",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.avatar.url)


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"}, required=False)
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"}, required=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "avatar",
            "password",
            "password_confirm",
        ]

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError("Passwords must match!")
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("password_confirm", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserProfileListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "organization",
            # "device_limit",
            # "current_device_count",
            "expiration_date",
        ]

    def get_user(self, obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "name": obj.user.username,
            }

    def get_organization(self, obj):
        if obj.organization:
            return {
                "id": obj.organization.id,
                "name": obj.organization.name,
            }


class UserProfileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class UserProfileRetrieveSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "organization",
            # "device_limit",
            # "current_device_count",
            "expiration_date",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_user(self, obj):
        if obj.user:
            return {
                "id": obj.user.id,
                "name": obj.user.username,
            }

    def get_organization(self, obj):
        if obj.organization:
            return {
                "id": obj.organization.id,
                "name": obj.organization.name,
            }


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "user",
            "organization",
            # "device_limit",
            # "current_device_count",
            "expiration_date",
            "is_active",
        ]

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserListForSelectSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['value', 'label']

    def get_value(self, obj):
        return obj.id

    def get_label(self, obj):
        return obj.username




class UserProfileSelectList(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['value', 'label']

    def get_value(self, obj):
        return obj.id

    def get_label(self, obj):
        if obj.user:
            return obj.user.username

