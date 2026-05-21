from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import serializers
from .models import Attachment, DeviceTimeReport


class AttachmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Attachment.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.AttachmentCreateSerializer
        return serializers.AttachmentSerializer


class AttachmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReportTimeAPI(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def post(self, request):
        device_id = request.data.get('device_id')
        device_time_str = request.data.get('current_time')  # ISO formatda

        if not device_id or not device_time_str:
            return Response({"error": "Data missing"}, status=400)

        # Qurilma vaqtini modelda yangilaymiz
        DeviceTimeReport.objects.update_or_create(
            device_id=device_id,
            defaults={'last_reported_time': device_time_str}
        )

        return Response({"status": "ok"})
