# users/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from apps.organizations.models import Organization
from apps.organizations.serializers import ensure_default_org_profile
from apps.users.serializers import ProfileSerializer, UserSerializer


@staff_member_required
def get_org_db_name(request):
    org_id = request.GET.get("org_id")
    try:
        org = Organization.objects.get(id=org_id)
        db_val = org.slug or slugify(org.name)
        return JsonResponse({"db_name": db_val})
    except Organization.DoesNotExist:
        return JsonResponse({"db_name": ""})


class AuthViewSet(ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)
            return Response(
                {
                    "token": access,
                    "access_token": access,
                    "refresh_token": str(refresh),
                    "users": UserSerializer(user).data,
                },
            )
        return Response(
            {"error": "Invalid Credentials"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        # Ensure profile and organization exist for consistent responses
        ensure_default_org_profile(user)
        data = ProfileSerializer(user).data
        return Response(data)
