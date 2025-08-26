from rest_framework.exceptions import APIException


class DeviceLimitReached(APIException):
    status_code = 403
    default_detail = "Device limit reached."
    default_code = "device_limit_reached"
