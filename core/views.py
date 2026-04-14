from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny]) # Xavfsizlik tekshiruvisiz hamma kirishi kerak
def server_discovery_ping(request):
    return Response({
        "status": "MEDIA-MANAGER",
        "server_name": "Media-Manager-Server",
        "version": "1.0.0"
    })