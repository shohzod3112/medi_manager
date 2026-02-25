import json
import sys
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

hwid = sys.argv[1]

payload = {
    "hwid": hwid,
    "expires_at": "2027-01-01"
}

data = json.dumps(payload, sort_keys=True).encode()

with open("private.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None,
        backend=default_backend()
    )

signature = private_key.sign(
    data,
    padding.PKCS1v15(),
    hashes.SHA256()
)

licence = {
    **payload,
    "signature": signature.hex()
}

with open("licence.json", "w") as f:
    json.dump(licence, f, indent=4)

print("licence.json created.")