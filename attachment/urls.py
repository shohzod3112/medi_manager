from django.urls import path
from . import views

urlpatterns = [
    path('', views.AttachmentListCreateAPIView.as_view(), name='attachment-list-create'),
    path('<int:pk>', views.AttachmentRetrieveUpdateDestroyAPIView.as_view(), name='attachment-detail'),

    path('<int:pk>', views.ReportTimeAPI.as_view(), name='attachment-detail'),
]
