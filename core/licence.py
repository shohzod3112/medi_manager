import json
import hashlib
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.exceptions import InvalidSignature

def get_server_hwid():
    with open("/etc/machine-id") as f:
        return hashlib.sha256(f.read().strip().encode()).hexdigest()

def check_license():
    with open("/licence/licence.json") as f:
        licence = json.load(f)

    payload = {
        "hwid": licence["hwid"],
        "expires_at": licence["expires_at"]
    }

    data = json.dumps(payload, sort_keys=True).encode()
    signature = bytes.fromhex(licence["signature"])

    with open("public.pem", "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except InvalidSignature:
        raise Exception("Licence signature invalid!")

    if licence["hwid"] != get_server_hwid():
        raise Exception("HWID mismatch!")

    if datetime.strptime(licence["expires_at"], "%Y-%m-%d") < datetime.now():
        raise Exception("Licence expired!")