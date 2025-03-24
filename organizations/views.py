from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions

from rest_framework import generics
from rest_framework.views import APIView

from core.models import User
from .models import Device, Playlist
from .serializers import DeviceSerializer, MediaSerializer, PlaylistSerializer


class PlaylistsDetailAPIView(APIView):

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

        response = {
            'start_time': playlist.start_time,
            'end_time': playlist.end_time,
            'exit_password': device.exit_password,
            'playlist': media_list
        }

        return Response(response, status=200)


class GetDeviceToken(APIView):
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
        data = request.data

        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Device registered successfully',
                    'device_id': serializer.data['device_id']
                 },
                status=201)
        return Response(serializer.errors, status=404)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


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
