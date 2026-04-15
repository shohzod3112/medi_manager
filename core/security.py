from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_server_keys():
    # Private key yaratish
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Private keyni string ko'rinishida saqlash (PEM)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Public keyni string ko'rinishida saqlash (PEM)
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return priv_pem.decode(), pub_pem.decode()

# Bu kalitlarni bir marta yaratib, .env yoki DBda saqlab qo'yish kerak.