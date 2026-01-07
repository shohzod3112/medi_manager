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

        # status code ga qarab log level tanlaymiz
        if response.status_code >= 500:
            log_func = logger.error
        else:
            log_func = logger.info

        log_func(
            "request",
            extra={
                "user": user,
                "method": request.method,
                "path": request.get_full_path(),
                "status": response.status_code,
                "headers": headers,
            },
        )
        return response
