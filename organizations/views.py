from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, APIException
from rest_framework.response import Response
from rest_framework import status, permissions

from rest_framework import generics
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from core.models import User
from .models import Device, Playlist
from .serializers import DeviceSerializer, MediaSerializer, PlaylistSerializer


class PlaylistsDetailAPIView(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="sn",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Serial number of the device",
                required=True
            ),
            openapi.Parameter(
                name="username",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Username of the device owner",
                required=True
            ),
            openapi.Parameter(
                name="token",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Device token",
                required=True,
            )
        ],
        responses={
            200: openapi.Response("Successful Response", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "token": openapi.Schema(type=openapi.TYPE_STRING, description="Device token")
                }
            )),
            400: openapi.Response("Bad Request"),
            404: openapi.Response("Token Not Found"),
        }
    )
    def get(self, *args, **kwargs):
        query_params = self.request.query_params
        sn = query_params.get('sn', None)
        username = query_params.get('username', None)
        token = query_params.get('token', None)

        if not sn and not username and not token:
            return Response({"error": "Serial Number, Username and Token is Required"}, status=400)

        if not sn:
            return Response({"error": "Serial Number is Required"}, status=400)

        if not username:
            return Response({"error": "Username is Required"}, status=400)

        if not token:
            return Response({"error": "Token is Required"}, status=400)

        user = User.objects.filter(username__iexact=username).first()
        if not user:
            return Response({"error": "User Not Found"}, status=404)

        device = Device.objects.filter(serial_number=sn, owner=user, token=token).first()
        if not device:
            return Response({"error": "Device Not Found"}, status=404)

        playlist = Playlist.objects.filter(devices=device).first()
        if not playlist:
            return Response({"error": "Playlist Not Found"}, status=404)

        media_list = []
        for media in playlist.media.all():
            media_list.append({
                'id': media.media_id,
                'name': media.name,
                'url': self.request.build_absolute_uri(media.file.url),
                'type': media.type,
                'duration': media.duration
            })

        playlists = []
        for playlist in Playlist.objects.filter(devices=device):
            playlists.append({
                'id': playlist.playlist_id,
                'name': playlist.name,
                'start_time': timezone.localtime(playlist.start_time).strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': timezone.localtime(playlist.end_time).strftime('%Y-%m-%d %H:%M:%S'),
                'medias': media_list
            })

        response = {
            'server_time': timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'exit_password': device.exit_password,
            'playlists': playlists
        }

        return Response(response, status=200)


class GetDeviceToken(APIView):

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="sn",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Serial number of the device",
                required=True
            ),
            openapi.Parameter(
                name="username",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Username of the device owner",
                required=True
            ),
        ],
    )
    def get(self, *args, **kwargs):
        params = self.request.query_params
        serial_number = params.get('sn', None)
        username = params.get('username', None)

        if not serial_number and not username:
            return Response({"error": "Username and Serial Number is Not Given"}, status=400)

        if not serial_number:
            return Response({'error': "Serial Number is Not Given"}, status=400)

        if not username:
            return Response({'error': "Username is Not Given"}, status=400)

        device = Device.objects.filter(serial_number=serial_number, owner__username__iexact=username).first()
        if device and device.token:
            return Response({"token": f"{device.token}"}, status=200)
        return Response({"error": "Token Not Found"}, status=404)


class RegisterDeviceView(generics.CreateAPIView):
    serializer_class = DeviceSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        try:
            serializer.is_valid(raise_exception=True)
            device = serializer.save()
            return Response(
                {
                    'success': True,
                    'message': 'Device registered successfully',
                    'device_id': device.device_id
                },
                status=status.HTTP_201_CREATED
            )

        except ValidationError as e:
            error_detail = e.detail
            first_error_key = list(error_detail.keys())[0]
            error_message = error_detail[first_error_key]

            if isinstance(error_message, list):
                error_message = error_message[0]

            if error_message in ["User not found"]:
                return Response({'success': False, 'error': {'code': 'USER_NOT_FOUND', 'message': error_message}},
                                status=status.HTTP_404_NOT_FOUND)

            if error_message in ["User's account has expired"]:
                return Response({'success': False, 'error': {'code': 'EXPIRED_ACCOUNT', 'message': error_message}},
                                status=status.HTTP_403_FORBIDDEN)

            if error_message in ["Device with this serial number already exists"]:
                return Response({'success': False, 'error': {'code': 'DUPLICATE_SN', 'message': error_message}},
                                status=status.HTTP_409_CONFLICT)

            return Response({'success': False, 'error': error_detail}, status=status.HTTP_400_BAD_REQUEST)

        except APIException as e:
            return Response({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Upload_media(generics.CreateAPIView):
    """
    Upload a new media file. The authenticated user is automatically assigned as the owner.
    """
    serializer_class = MediaSerializer
    permission_classes = (permissions.IsAuthenticated,)


    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['owner'] = request.user.id

        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Media uploaded successfully', 'media_id': serializer.data['media_id']},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_playlist(request):
    data = request.data.copy()
    data['owner'] = request.user.id  # Auto-assign the owner

    serializer = PlaylistSerializer(data=data)
    if serializer.is_valid():
        playlist = serializer.save()

        # Add media and devices
        if 'media' in data:
            playlist.media.set(data['media'])
        if 'devices' in data:
            playlist.devices.set(data['devices'])

        return Response(
            {'message': 'Playlist created successfully', 'playlist_id': playlist.playlist_id}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def sync_device(request, serial_number):
    """
    Sync a device with its assigned playlists. Only the device's owner can sync it.
    """
    try:
        device = Device.objects.get(serial_number=serial_number, owner=request.user)
        assigned_playlists = Playlist.objects.filter(devices=device)  # Uses ManyToMany relationship
        playlist_data = PlaylistSerializer(assigned_playlists, many=True).data
        return Response({
            'message': 'Device sync successful',
            'playlists': playlist_data
        }, status=status.HTTP_200_OK)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found or not assigned to this user'}, status=status.HTTP_400_BAD_REQUEST)
