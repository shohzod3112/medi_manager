from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from ..users.models import User, UserProfile
from .models import Device, Media, Organization, Playlist
from .permissions import IsOrgAndProfileActive
from .serializers import (
    DeviceSerializer,
    MediaSerializer,
    OrganizationSerializer,
    PlaylistSerializer,
)


class OrganizationAdminViewSet(ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (permissions.IsAdminUser,)

    @action(
        detail=True,
        methods=["post"],
        url_path="assign-user",
        permission_classes=[permissions.IsAdminUser],
    )
    def assign_user(self, request, pk=None):
        org = self.get_object()
        user_id = request.data.get("user_id")
        username = request.data.get("username")
        device_limit = request.data.get("device_limit")
        is_active = request.data.get("is_active")
        expiration_date = request.data.get("expiration_date")

        if not user_id and not username:
            return Response(
                {"error": "user_id or username is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        try:
            if user_id:
                user = UserModel.objects.get(id=user_id)
            else:
                user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"organization": org},
        )
        if not created and profile.organization_id != org.id:
            if profile.current_device_count > 0:
                return Response(
                    {
                        "error": "Cannot move user to another organization while they have registered devices",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Move user to this organization
            profile.organization = org
        # Apply optional fields
        if device_limit is not None:
            try:
                profile.device_limit = int(device_limit)
            except (TypeError, ValueError):
                return Response(
                    {"error": "device_limit must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if is_active is not None:
            profile.is_active = (
                bool(is_active)
                if isinstance(is_active, bool)
                else str(is_active).lower() in ["true", "1", "yes"]
            )
        if expiration_date:
            from django.utils.dateparse import parse_date

            parsed = (
                parse_date(expiration_date)
                if isinstance(expiration_date, str)
                else expiration_date
            )
            if not parsed:
                return Response(
                    {"error": "Invalid expiration_date format (expected YYYY-MM-DD)"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            profile.expiration_date = parsed

        # Validate org capacity and user constraints via clean()
        try:
            profile.save()
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "User assigned to organization",
                "user_id": user.id,
                "organization": org.id,
            },
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="unassign-user",
        permission_classes=[permissions.IsAdminUser],
    )
    def unassign_user(self, request, pk=None):
        org = self.get_object()
        user_id = request.data.get("user_id")
        username = request.data.get("username")
        if not user_id and not username:
            return Response(
                {"error": "user_id or username is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        try:
            if user_id:
                user = UserModel.objects.get(id=user_id)
            else:
                user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            profile = UserProfile.objects.get(user=user, organization=org)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User is not assigned to this organization"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if profile.current_device_count > 0:
            return Response(
                {"error": "Cannot unassign user who still has registered devices"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.delete()
        return Response(
            {
                "message": "User unassigned from organization",
                "user_id": user.id,
                "organization": org.id,
            },
        )


class PlaylistViewSet(ModelViewSet):
    serializer_class = PlaylistSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgAndProfileActive)

    def get_permissions(self):
        if getattr(self, "action", None) == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOrgAndProfileActive()]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if not profile or not profile.organization_id:
            return Playlist.objects.none()
        return Playlist.objects.filter(
            organization=profile.organization,
            owner=user,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        # Serializer handles owner/org assignment
        serializer.save()


class MediaViewSet(ModelViewSet):
    serializer_class = MediaSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrgAndProfileActive)

    def get_permissions(self):
        if getattr(self, "action", None) == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOrgAndProfileActive()]

    def get_queryset(self):
        user = self.request.user
        profile = getattr(user, "profile", None)
        if not profile or not profile.organization_id:
            return Media.objects.none()
        return Media.objects.filter(
            organization=profile.organization,
            owner=user,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        # Serializer handles owner/org assignment
        serializer.save()


class DeviceViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "serial_number"

    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            return Device.objects.none()
        return Device.objects.filter(user_profile__user=user).select_related(
            "user_profile",
            "organization",
        )

    def get_permissions(self):
        # Allow unauthenticated access for playlist-detail action (token-based)
        if getattr(self, "action", None) == "playlist_detail":
            return [AllowAny()]
        # For device creation, allow authenticated users; serializer will provision org/profile if needed
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        # Backward-compatible: accept minimal payload and ignore unknown fields like 'owner'
        data = request.data.copy()
        data.pop("owner", None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Device registered successfully",
                "device_id": str(device.id),
                "token": device.token,
            },
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, *args, **kwargs):
        device = self.get_object()
        if not device.token:
            return Response(
                {"error": "Token not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"token": device.token}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="sync")
    def sync(self, request, serial_number=None, pk=None):
        """
        Sync a device with its assigned playlists. Only the device's owner can sync it.
        """
        device = self.get_object()
        if device.user_profile.user_id != request.user.id:
            return Response(
                {"error": "Device not found or not assigned to this user"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Organization and profile checks
        profile = device.user_profile
        org = device.organization
        if not profile.is_active or profile.is_expired():
            return Response(
                {"error": "User profile is inactive or expired"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not org.is_active or org.is_expired():
            return Response(
                {"error": "Organization is inactive or expired"},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        assigned_playlists = Playlist.objects.filter(
            devices=device,
            is_active=True,
            start_time__lte=now,
            end_time__gte=now,
        )
        playlist_data = PlaylistSerializer(assigned_playlists, many=True).data
        return Response(
            {"message": "Device sync successful", "playlists": playlist_data},
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="sn",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Serial number of the device",
                required=True,
            ),
            openapi.Parameter(
                name="username",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Username of the device owner",
                required=True,
            ),
            openapi.Parameter(
                name="token",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Device token",
                required=True,
            ),
        ],
        responses={
            200: openapi.Response(
                "Successful Response",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "token": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Device token",
                        ),
                    },
                ),
            ),
            400: openapi.Response("Bad Request"),
            404: openapi.Response("Token Not Found"),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="playlist-detail",
        permission_classes=[AllowAny],
    )
    def playlist_detail(self, request):
        query_params = request.query_params
        sn = query_params.get("sn", None)
        username = query_params.get("username", None)
        token = query_params.get("token", None)

        if not sn and not username and not token:
            return Response(
                {"error": "Serial Number, Username and Token is Required"},
                status=400,
            )

        if not sn:
            return Response({"error": "Serial Number is Required"}, status=400)

        if not username:
            return Response({"error": "Username is Required"}, status=400)

        if not token:
            return Response({"error": "Token is Required"}, status=400)

        users = User.objects.filter(username__iexact=username).first()
        if not users:
            return Response({"error": "User Not Found"}, status=404)

        device = Device.objects.filter(
            serial_number=sn,
            user_profile__user=users,
            token=token,
        ).first()
        if not device:
            return Response({"error": "Device Not Found"}, status=404)

        # Organization and profile checks
        profile = device.user_profile
        org = device.organization
        if not profile.is_active or profile.is_expired():
            return Response(
                {"error": "User profile is inactive or expired"},
                status=403,
            )
        if not org.is_active or org.is_expired():
            return Response(
                {"error": "Organization is inactive or expired"},
                status=403,
            )

        now = timezone.now()
        playlists = Playlist.objects.filter(
            devices=device,
            is_active=True,
            start_time__lte=now,
            end_time__gte=now,
        )
        if not playlists.exists():
            return Response({"error": "Playlist Not Found"}, status=404)

        playlists_data = []
        for playlist in playlists.order_by("start_time"):
            media_list = []
            for media in playlist.media.all():
                media_list.append(
                    {
                        "id": media.media_id,
                        "name": media.name,
                        "url": request.build_absolute_uri(media.file.url),
                        "type": media.type,
                        "duration": media.duration,
                    },
                )

            playlists_data.append(
                {
                    "id": playlist.playlist_id,
                    "name": playlist.name,
                    "start_time": timezone.localtime(playlist.start_time).strftime(
                        "%Y-%m-%d %H:%M:%S",
                    ),
                    "end_time": timezone.localtime(playlist.end_time).strftime(
                        "%Y-%m-%d %H:%M:%S",
                    ),
                    "medias": media_list,
                },
            )

        response = {
            "server_time": timezone.localtime(timezone.now()).strftime(
                "%Y-%m-%d %H:%M:%S",
            ),
            "exit_password": device.exit_password,
            "id": device.organization_device_id,
            "name": device.name,
            "playlists": playlists_data,
        }

        return Response(response, status=200)
