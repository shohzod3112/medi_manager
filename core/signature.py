import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from django.conf import settings

# 1. Qurilmaning PRIVATE KEY'i (Buni o'zingizda generatsiya qilganingiz deb hisoblaymiz)
# Agar yo'q bo'lsa, avvalgi generate_server_keys funksiyasidan foydalaning
private_key_pem = os.getenv("SERVER_PRIVATE_KEY")

priv_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)

# 2. device_id ni imzolash
device_id = "ABC123"
signature = priv_key.sign(
    device_id.encode(),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

print(base64.b64encode(signature).decode())