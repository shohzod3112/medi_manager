from rest_framework import generics, permissions
from .models import Attachment
from .serializers import AttachmentSerializer


class AttachmentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class AttachmentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
