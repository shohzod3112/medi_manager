# users/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.utils.text import slugify
from rest_framework import status, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from apps.users.models import UserProfile
from apps.users.models.user import User
from apps.organizations.models import Organization
from apps.organizations.serializers import ensure_default_org_profile
from apps.users.serializers import ProfileSerializer, UserSerializer
from apps.users.serializers import user as user_serializer
from apps.users.serializers.user import LoginSerializer
from core.paginations import CustomPagination

# permission dagi barchasini IsAdminUser ga o'girish kerak


@staff_member_required
def get_org_db_name(request):
    org_id = request.GET.get("org_id")
    try:
        org = Organization.objects.get(id=org_id)
        db_val = org.slug or slugify(org.name)
        return JsonResponse({"db_name": db_val})
    except Organization.DoesNotExist:
        return JsonResponse({"db_name": ""})


class LoginAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"error": "Username va password majburiy"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Noto‘g‘ri login yoki parol"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        return Response(
            {
                "success": True,
                "message": "Login muvaffaqiyatli amalga oshirildi",
                "access_token": access,
                "refresh_token": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class WhoAmIAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        # Ensure profile and organization exist for consistent responses
        ensure_default_org_profile(user)
        data = ProfileSerializer(user).data
        return Response(data)

class UserListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return user_serializer.UserCreateSerializer
        return user_serializer.UserListSerializer


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return user_serializer.UserRetrieveSerializer
        return user_serializer.UserUpdateSerializer


class UserProfileListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    queryset = UserProfile.objects.select_related("user", "organization")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return user_serializer.UserProfileListSerializer
        return user_serializer.UserProfileCreateSerializer


class UserProfileRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    queryset = UserProfile.objects.select_related("user", "organization")

    def get_serializer_class(self):
        if self.request.method == "GET":
            return user_serializer.UserProfileRetrieveSerializer
        return user_serializer.UserProfileUpdateSerializer

class UserListForSelectAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = user_serializer.UserListForSelectSerializer


class UserProfileSelectListAPIView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = user_serializer.UserProfileSelectList
