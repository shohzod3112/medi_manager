from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException


class DeviceLimitReached(APIException):
    status_code = 403
    default_detail = 'Device limit reached.'
    default_code = 'device_limit_reached'
