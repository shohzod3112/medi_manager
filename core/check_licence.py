import json
import hmac
import hashlib
from datetime import datetime

SECRET = b"LOCAL_MEDIA_MANAGER_SECRET"
LICENCE_PATH = "/opt/media-manager/licence/licence.json"


def verify_signature(data, signature):
    raw = json.dumps(data, sort_keys=True).encode()
    expected = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def get_hwid():
    with open("/etc/machine-id") as f:
        mid = f.read().strip()

    return hashlib.sha256(mid.encode()).hexdigest()


def check_licence():
    with open(LICENCE_PATH) as f:
        lic = json.load(f)

    signature = lic.pop("signature")

    if not verify_signature(lic, signature):
        raise Exception("Invalid licence signature")

    if lic["hwid"] != get_hwid():
        raise Exception("HWID mismatch")

    exp = datetime.strptime(lic["expires"], "%Y-%m-%d").date()

    if exp < datetime.now().date():
        raise Exception("Licence expired")

    return True

if __name__ == "__main__":
    import sys

    try:
        check_licence()
        print("✅ License OK")
        sys.exit(0)
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)