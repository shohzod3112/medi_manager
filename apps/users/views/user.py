# users/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework_simplejwt.tokens import RefreshToken
from apps.organizations.models import Organization
from apps.users.serializers import UserSerializer


@staff_member_required
def get_org_db_name(request):
    org_id = request.GET.get('org_id')
    try:
        org = Organization.objects.get(id=org_id)
        return JsonResponse({'db_name': org.db_name})
    except Organization.DoesNotExist:
        return JsonResponse({'db_name': ''})


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'users': UserSerializer(user).data
        })
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
