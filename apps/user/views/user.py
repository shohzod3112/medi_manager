# user/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def get_org_db_name(request):
    org_id = request.GET.get('org_id')
    try:
        org = Organization.objects.get(id=org_id)
        return JsonResponse({'db_name': org.db_name})
    except Organization.DoesNotExist:
        return JsonResponse({'db_name': ''})


@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)
