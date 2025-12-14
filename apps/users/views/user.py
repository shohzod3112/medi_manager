# users/views.py
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.db.models import Q
from django.http import JsonResponse
from django.utils.text import slugify
from rest_framework import status, generics
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from core.permissions import OrganizationActivePermission

from apps.users.models.user import User
from apps.organizations.models import Organization
from apps.users.serializers import ProfileSerializer, UserSerializer
from apps.users.serializers import user as user_serializer
from apps.users.serializers.user import LoginSerializer, WhoAmISerializer
from core.paginations import CustomPagination

# permission dagi barchasini IsAdminUser ga o'girish kerak


@staff_member_required
def get_org_db_name(request):
    org_id = request.GET.get("org_id")
    try:
        org = Organization.objects.get(id=org_id)
        db_val = org.name or slugify(org.name)
        return JsonResponse({"db_name": db_val})
    except Organization.DoesNotExist:
        return JsonResponse({"db_name": ""})


class LoginAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
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

        if getattr(user, "role", None) != "superadmin":
            org = getattr(user, "organization", None)
            if not org:
                raise AuthenticationFailed("Tashkilot biriktirilmagan!")
            if not org.is_active:
                raise AuthenticationFailed("Tashkilot faol emas!")
            if org.expiration_date and org.expiration_date < timezone.now().date():
                raise AuthenticationFailed("Tashkilotning obuna muddati tugagan!")

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        return Response(
            {
                "success": True,
                "message": "Login muvaffaqiyatli amalga oshirildi",
                "access_token": access,
                "refresh_token": str(refresh),
                "user": UserSerializer(user).data,
                "fullname": f"{user.first_name or ''} {user.last_name or ''}".strip(),
                "role": user.role,
            },
            status=status.HTTP_200_OK,
        )


class MeAPIView(APIView):
    permission_classes = [OrganizationActivePermission]
    def get(self, request):
        user = request.user
        # Ensure profile and organization exist for consistent responses
        # ensure_default_org_profile(user)
        data = ProfileSerializer(user).data
        return Response(data)


class WhoAmIAPIView(APIView):
    permission_classes = [OrganizationActivePermission]
    def get(self, request):
        user = request.user
        serializer = WhoAmISerializer(user)
        return Response(serializer.data)


class UserListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAdminUser]
    pagination_class = CustomPagination
    queryset = User.objects.select_related("organization")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return user_serializer.UserCreateSerializer
        return user_serializer.UserListSerializer

    def get_queryset(self):
        organization = self.request.query_params.get("organization")
        name = self.request.query_params.get("name")
        login = self.request.query_params.get("login")
        is_active = self.request.query_params.get("is_active")

        queryset = self.queryset

        if organization:
            queryset = queryset.filter(organization=organization)
        if name:
            queryset = queryset.filter(
                Q(first_name__icontains=name) | Q(last_name__icontains=name)
            )
        if login:
            queryset = queryset.filter(username__icontains=login)

        queryset = queryset.filter(is_active=True) if is_active == "true" else queryset.filter(is_active=False) if is_active == "false" else queryset

        return queryset

    def perform_create(self, serializer):
        role = self.request.data.get("role")

        if role == "superadmin":
            serializer.save(is_superuser=True, is_staff=True)
        elif role == "admin":
            serializer.save(is_superuser=False, is_staff=True)
        else:
            serializer.save(is_superuser=False, is_staff=True)


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == "GET":
            return user_serializer.UserRetrieveSerializer
        return user_serializer.UserUpdateSerializer


class UserListForSelectAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = user_serializer.UserListForSelectSerializer
