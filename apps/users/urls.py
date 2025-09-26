from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from .views import user as user_views

app_name = "users"

# Router-based endpoints for auth
router = DefaultRouter()
router.register(r"auth", views.AuthViewSet, basename="auth")

urlpatterns = [
    # Backward-compatible explicit endpoints
    path("login/", views.AuthViewSet.as_view({"post": "login"}), name="login"),
    path("me/", views.WhoAmIAPIView.as_view(), name="me"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("admin/get-org-db-name/", views.get_org_db_name, name="get_org_db_name"),
    # Router URLs
    path("", include(router.urls)),

    path("users", user_views.UserListCreateAPIView.as_view()),
    path("users/<int:pk>", user_views.UserRetrieveUpdateDestroyAPIView.as_view()),
    path("users-select", user_views.UserListForSelectAPIView.as_view()),

    path("user-profiles", user_views.UserProfileListCreateAPIView.as_view()),
    path("user-profiles/<int:pk>", user_views.UserProfileRetrieveUpdateDestroyAPIView.as_view()),
    path("user-profiles-select", user_views.UserProfileSelectListAPIView.as_view()),
]
