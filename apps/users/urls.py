from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .views import user as user_views

app_name = "users"


urlpatterns = [
    # Backward-compatible explicit endpoints
    path(f"{app_name}/login", user_views.LoginAPIView.as_view(), name="login"),
    path(f"{app_name}/me", views.WhoAmIAPIView.as_view(), name="me"),
    path(f"{app_name}/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path(f"{app_name}/admin/get-org-db-name", views.get_org_db_name, name="get_org_db_name"),

    path(f"{app_name}", user_views.UserListCreateAPIView.as_view()),
    path(f"{app_name}/<int:pk>", user_views.UserRetrieveUpdateDestroyAPIView.as_view()),
    path(f"{app_name}/select", user_views.UserListForSelectAPIView.as_view()),

    path(f"{app_name}/user-profiles", user_views.UserProfileListCreateAPIView.as_view()),
    path(f"{app_name}/user-profiles/<int:pk>", user_views.UserProfileRetrieveUpdateDestroyAPIView.as_view()),
    path(f"{app_name}/user-profiles-select", user_views.UserProfileSelectListAPIView.as_view()),
]
