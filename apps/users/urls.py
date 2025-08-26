from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("auth/login/", views.AuthViewSet.as_view({"post": "login"}), name="login"),
    path("auth/me/", views.AuthViewSet.as_view({"get": "me"}), name="me"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("admin/get-org-db-name/", views.get_org_db_name, name="get_org_db_name"),
]
