import hmac
import hashlib
import os
import time
from rest_framework.exceptions import AuthenticationFailed

SECRET_KEY = os.getenv("SECRET_KEY")

def verify_request_security(request):
    timestamp = request.headers.get('X-Timestamp')
    signature = request.headers.get('X-Signature')

    if not timestamp or not signature:
        raise AuthenticationFailed("Xavfsizlik ma'lumotlari yetishmayapti")

    # 1. Replay Attack tekshiruvi
    server_now = int(time.time())
    if abs(server_now - int(timestamp)) > 30:
        raise AuthenticationFailed("So'rov vaqti o'tib ketgan (Replay Attack)")

    # 2. MITM (Imzo) tekshiruvi
    # So'rov yo'li va vaqtni birlashtirib imzo yaratamiz
    message = f"{request.path}{timestamp}".encode()
    expected_signature = hmac.new(SECRET_KEY, message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise AuthenticationFailed("Imzo noto'g'ri (MITM Attack)")