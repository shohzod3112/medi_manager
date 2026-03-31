import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("app")

SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
}

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        user = request.user.id if request.user.is_authenticated else "anonymous"
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in SENSITIVE_HEADERS
        }

        # status code-ga qarab alohida handler ishlaydi
        if response.status_code >= 500:
            logger.error(
                "Request failed",
                extra={
                    "user": user,
                    "method": request.method,
                    "path": request.get_full_path(),
                    "status": response.status_code,
                    "headers": headers,
                },
            )
        else:
            logger.info(
                "Request",
                extra={
                    "user": user,
                    "method": request.method,
                    "path": request.get_full_path(),
                    "status": response.status_code,
                    "headers": headers,
                },
            )
        return response