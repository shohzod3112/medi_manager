from rest_framework import generics, permissions

from . import serializers
from .models import Attachment


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
