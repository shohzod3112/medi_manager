from django.db.models import Q, F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny

from core.paginations import CustomPagination
from ..users.models import User
from .models import Device, File, Organization, Playlist, DeviceType
from .permissions import IsOrgAndProfileActive
from core.permissions import OrganizationActivePermission
from . import serializers
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response


class DeviceListCreateAPIView(generics.ListCreateAPIView):
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Device.objects.filter(organization=self.request.user.organization).select_related(
            "organization", 'device_type'
        )
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        serial_number = self.request.query_params.get("serial_number", None)
        if serial_number:
            queryset = queryset.filter(serial_number__icontains=serial_number)
        device_type = self.request.query_params.get("device_type", None)
        if device_type:
            queryset = queryset.filter(device_type=device_type)
        organization = self.request.query_params.get("organization", None)
        if organization:
            queryset = queryset.filter(organization=organization)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.DeviceCreateSerializer
        return serializers.DeviceListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.AllowAny()]
        return [OrganizationActivePermission()]

    def get_authenticators(self):
        if self.request.method == "POST":
            return []  # POST uchun autentifikatsiya tekshiruvini o'chiradi
        return super().get_authenticators()

    def create(self, request, *args, **kwargs):
        username = request.data.get('username', None)
        if username:
            try:
                user = User.objects.get(username=username)
                org = user.organization
                if org.has_reached_device_limit():
                    return Response({"detail": "Device soni limitdan oshib ketti!"}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"detail": "Username not found"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        return Response(serializer.to_representation(device), status=status.HTTP_201_CREATED)


class DeviceRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [OrganizationActivePermission]
    queryset = Device.objects.select_related('organization', 'device_type')

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.DeviceRetrieveSerializer
        return serializers.DeviceUpdateSerializer

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user
        )


class DeviceDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    queryset = Device.objects.all()
    serializer_class = serializers.GetTokenSerializer
    lookup_field = "serial_number"

    def retrieve(self, request, *args, **kwargs):
        device = self.get_object()
        if not device or not device.token:
            return Response({"error": "Device or Token not found"}, status=404)
        return Response({"token": device.token}, status=200)


class DeviceSyncAPIView(APIView):
    permission_classes = [OrganizationActivePermission]

    def get(self, request, serial_number):
        device = get_object_or_404(Device, serial_number=serial_number, organization=request.user.organization)
        org = device.organization

        # Profil yoki tashkilot faol emas yoki muddati o'tgan
        if not request.user.is_active:
            return Response({"error": "User is inactive or expired"}, status=403)
        if not org.is_active or org.is_expired():
            return Response({"error": "Organization is inactive or expired"}, status=403)

        now = timezone.localtime()

        event_playlists = Playlist.objects.filter(
            devices=device,
            is_active=True,
            type="event",
            start_date__lte=now.date(),
            end_date__gte=now.date(),
        ).filter(
            Q(start_time__lte=now.time(), end_time__gte=now.time()) |
            (
                    Q(start_time__gt=F("end_time")) &
                    (Q(start_time__lte=now.time()) | Q(end_time__gte=now.time()))
            )
        )

        if event_playlists.exists():
            selected_playlists = event_playlists
        else:
            selected_playlists = Playlist.objects.filter(
                devices=device,
                is_active=True,
                type="permanent",
            ).filter(
                Q(start_time__lte=now.time(), end_time__gte=now.time()) |
                (
                        Q(start_time__gt=F("end_time")) &
                        (Q(start_time__lte=now.time()) | Q(end_time__gte=now.time()))
                )
            )

        playlist_data = serializers.PlaylistSerializer(selected_playlists, many=True).data

        return Response(
            {"message": "Device sync successful", "playlists": playlist_data},
            status=status.HTTP_200_OK,
        )


class PlaylistDetailAPIView(APIView):
    permission_classes = [OrganizationActivePermission]

    def get(self, request):
        sn = request.query_params.get("sn")
        username = request.query_params.get("username")
        token = request.query_params.get("token")

        if not all([sn, username, token]):
            return Response(
                {"success": False, "message": "Serial Number, Username va Token majburiy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return Response({"success": False, "message": "User Not Found"}, status=404)

        device = Device.objects.filter(
            serial_number=sn,
            organization=user.organization,
            token=token,
        ).first()
        if not device:
            return Response({"success": False, "message": "Device Not Found"}, status=404)

        org = device.organization
        if not user.is_active:
            return Response({"success": False, "message": "User inactive"}, status=403)
        if not org.is_active or org.is_expired():
            return Response({"success": False, "message": "Organization inactive"}, status=403)

        now = timezone.localtime()

        event_playlists = Playlist.objects.filter(
            devices=device,
            is_active=True,
            type="event",
            start_date__lte=now.date(),
            end_date__gte=now.date(),
        ).filter(
            Q(start_time__lte=now.time(), end_time__gte=now.time()) |
            (
                Q(start_time__gt=F("end_time")) &
                (Q(start_time__lte=now.time()) | Q(end_time__gte=now.time()))
            )
        )

        if event_playlists.exists():
            active_playlists = event_playlists
        else:
            active_playlists = Playlist.objects.filter(
                devices=device,
                is_active=True,
                type="permanent",
            ).filter(
                Q(start_time__lte=now.time(), end_time__gte=now.time()) |
                (
                    Q(start_time__gt=F("end_time")) &
                    (Q(start_time__lte=now.time()) | Q(end_time__gte=now.time()))
                )
            ).order_by("-created_at")

        if not active_playlists.exists():
            return Response({"success": False, "message": "Playlist Not Found"}, status=404)

        playlists_data = []
        for playlist in active_playlists.order_by("start_time"):
            media_list = [
                {
                    "id": media.file_id,
                    "name": media.name,
                    "url": request.build_absolute_uri(media.file.url),
                    "type": media.type,
                    "duration": media.duration,
                }
                for media in playlist.file.all()
            ]

            playlists_data.append(
                {
                    "id": playlist.playlist_id,
                    "name": playlist.name,
                    "type": playlist.playlist_type,
                    "start_time": timezone.localtime(playlist.start_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": timezone.localtime(playlist.end_time).strftime("%Y-%m-%d %H:%M:%S"),
                    "medias": media_list,
                }
            )

        return Response(
            {
                "success": True,
                "message": "Playlist data loaded successfully",
                "server_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "device": {
                    "id": device.organization_device_id,
                    "name": device.name,
                    "exit_password": device.exit_password,
                },
                "playlists": playlists_data,
            },
            status=status.HTTP_200_OK,
        )


class FileSelectListAPIView(generics.ListAPIView):
    permission_classes = [OrganizationActivePermission]
    serializer_class = serializers.FileSelectListSerializer

    def get_queryset(self):
        queryset = File.objects.filter(organization=self.request.user.organization)
        return queryset


class DeviceSelectListAPIView(generics.ListAPIView):
    permission_classes = [OrganizationActivePermission]
    serializer_class = serializers.DeviceSelectListSerializer

    def get_queryset(self):
        queryset = Device.objects.filter(organization=self.request.user.organization)
        return queryset



class DeviceTypeListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination
    queryset = DeviceType.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.DeviceTypeSerializer
        return serializers.DeviceTypeListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DeviceTypeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = DeviceType.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return serializers.DeviceTypeSerializer
        return serializers.DeviceTypeListSerializer

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class DeviceTypeSelectListAPIView(generics.ListAPIView):
    permission_classes = [OrganizationActivePermission]
    queryset = DeviceType.objects.all()
    serializer_class = serializers.DeviceTypeSelectListSerializer


# CRUD for Organization
class OrganizationListCreateView(generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    permission_classes = [OrganizationActivePermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = Organization.objects.all()
        ex_date = self.request.query_params.get("ex_date", None)
        if ex_date:
            queryset = queryset.filter(expiration_date=ex_date)
        is_active = self.request.query_params.get("is_active", None)
        if is_active == "true":
            queryset = queryset.filter(is_active=True)
        elif is_active == "false":
            queryset = queryset.filter(is_active=False)
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.OrganizationSerializer
        return serializers.OrganizationListSerializer

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user
        )


class OrganizationRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer
    permission_classes = [OrganizationActivePermission]

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return serializers.OrganizationSerializer
        return serializers.OrganizationDetailSerializer

    def perform_update(self, serializer):
        serializer.save(
            updated_by=self.request.user
        )


# Assign user
# class AssignUserToOrganizationView(APIView):
#     permission_classes = [permissions.IsAdminUser]
#
#     def post(self, request, pk):
#         org = generics.get_object_or_404(Organization, pk=pk)
#         user_id = request.data.get("user_id")
#         username = request.data.get("username")
#         device_limit = request.data.get("device_limit")
#         is_active = request.data.get("is_active")
#         expiration_date = request.data.get("expiration_date")
#
#         if not user_id and not username:
#             return Response({"error": "user_id or username is required"},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         UserModel = get_user_model()
#         try:
#             user = UserModel.objects.get(id=user_id) if user_id else UserModel.objects.get(username=username)
#         except UserModel.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         # profile, created = UserProfile.objects.get_or_create(
#         #     user=user, defaults={"organization": org}
#         # )
#         #
#         # if not created and profile.organization_id != org.id:
#         #     if profile.current_device_count > 0:
#         #         return Response({"error": "Cannot move user with devices"},
#         #                         status=status.HTTP_400_BAD_REQUEST)
#         #     profile.organization = org
#
#         # # Optional fields
#         # if device_limit is not None:
#         #     try:
#         #         profile.device_limit = int(device_limit)
#         #     except (TypeError, ValueError):
#         #         return Response({"error": "device_limit must be an integer"},
#         #                         status=status.HTTP_400_BAD_REQUEST)
#
#         # if is_active is not None:
#         #     profile.is_active = (
#         #         bool(is_active) if isinstance(is_active, bool)
#         #         else str(is_active).lower() in ["true", "1", "yes"]
#         #     )
#
#         # if expiration_date:
#         #     parsed = parse_date(expiration_date) if isinstance(expiration_date, str) else expiration_date
#         #     if not parsed:
#         #         return Response({"error": "Invalid expiration_date (YYYY-MM-DD)"},
#         #                         status=status.HTTP_400_BAD_REQUEST)
#         #     profile.expiration_date = parsed
#         #
#         # try:
#         #     profile.save()
#         # except Exception as e:
#         #     return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         #
#         # return Response({
#         #     "message": "User assigned to organization",
#         #     "user_id": user.id,
#         #     "organization": org.id,
#         # })


# Unassign user
# class UnassignUserFromOrganizationView(APIView):
#     permission_classes = [permissions.IsAdminUser]
#
#     def post(self, request, pk):
#         org = generics.get_object_or_404(Organization, pk=pk)
#         user_id = request.data.get("user_id")
#         username = request.data.get("username")
#
#         if not user_id and not username:
#             return Response({"error": "user_id or username is required"},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         UserModel = get_user_model()
#         try:
#             user = UserModel.objects.get(id=user_id) if user_id else UserModel.objects.get(username=username)
#         except UserModel.DoesNotExist:
#             return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#
#         try:
#             profile = UserProfile.objects.get(user=user, organization=org)
#         except UserProfile.DoesNotExist:
#             return Response({"error": "User not assigned to this organization"},
#                             status=status.HTTP_404_NOT_FOUND)
#
#         if profile.current_device_count > 0:
#             return Response({"error": "Cannot unassign user with devices"},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         profile.delete()
#         return Response({
#             "message": "User unassigned from organization",
#             "user_id": user.id,
#             "organization": org.id,
#         })


class OrganizationSelectListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Organization.objects.all()
    serializer_class = serializers.OrganizationSelectSerializer


class PlaylistListCreateView(generics.ListCreateAPIView):
    serializer_class = serializers.PlaylistSerializer
    permission_classes = [OrganizationActivePermission]
    pagination_class = CustomPagination

    def get_queryset(self):
        user = self.request.user
        if not user.organization:
            return Playlist.objects.none()

        return Playlist.objects.filter(
            organization=user.organization,
            owner=user,
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save()


class PlaylistDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.PlaylistSerializer
    permission_classes = [OrganizationActivePermission]

    def get_queryset(self):
        user = self.request.user
        if user.organization:
            return Playlist.objects.none()

        return Playlist.objects.filter(
            organization=user.organization
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)



class FileListCreateView(generics.ListCreateAPIView):
    serializer_class = serializers.FileSerializer
    permission_classes = [OrganizationActivePermission]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.FileSerializer
        return serializers.FileListSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.organization:
            return File.objects.none()

        return File.objects.filter(
            organization=user.organization
        ).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        if request.data.get("attachment") is None:
            return Response({"error": "Attachment required"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.FileSerializer
    permission_classes = [OrganizationActivePermission]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return serializers.FileListSerializer
        return serializers.FileSerializer

    def get_queryset(self):
        user = self.request.user

        if not user.organization:
            return File.objects.none()

        return File.objects.filter(
            organization=user.organization,
            owner=user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
