from django.http import HttpResponseForbidden
from core.check_licence import check_licence


class LicenceCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Har bir API so'rovida litsenziya va vaqtni tekshiramiz [cite: 38, 74]
        if not check_licence():
            return HttpResponseForbidden("Licence error. Access denied.")

        return self.get_response(request)