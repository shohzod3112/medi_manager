from django.urls import path
from .views import AttachmentListCreateAPIView, AttachmentRetrieveUpdateDestroyAPIView

urlpatterns = [
    path('', AttachmentListCreateAPIView.as_view(), name='attachment-list-create'),
    path('<int:pk>', AttachmentRetrieveUpdateDestroyAPIView.as_view(), name='attachment-detail'),
]
