import os
from pathlib import Path

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


def set_key_to_env(key: str, value: str):
    """ .env fayliga kalitni yozadi yoki bor bo'lsa yangilaydi """
    env_path = Path('.env')

    # Agar .env fayli bo'lmasa, yaratamiz
    if not env_path.exists():
        env_path.touch()

    lines = env_path.read_text().splitlines()
    key_found = False
    new_lines = []

    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f'{key}="{value}"')
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        new_lines.append(f'{key}="{value}"')

    env_path.write_text("\n".join(new_lines) + "\n")


def ensure_server_keys():
    # settings'dan yoki os.environ'dan tekshiramiz
    if not os.getenv("SERVER_PRIVATE_KEY") or not os.getenv("SERVER_PUBLIC_KEY"):
        from .security import generate_server_keys  # o'zingiz yozgan funksiya

        priv, pub = generate_server_keys()

        # .env fayliga yozamiz
        set_key_to_env("SERVER_PRIVATE_KEY", priv)
        set_key_to_env("SERVER_PUBLIC_KEY", pub)

        # Hozirgi ishlayotgan sessiyaga ham qo'shib qo'yamiz
        os.environ["SERVER_PRIVATE_KEY"] = priv
        os.environ["SERVER_PUBLIC_KEY"] = pub

        print("🚀 Server uchun yangi kalitlar yaratildi va .env ga saqlandi!")
    else:
        print("✅ Server kalitlari allaqachon mavjud.")