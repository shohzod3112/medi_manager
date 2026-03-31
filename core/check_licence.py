import json
import hmac
import hashlib
from datetime import datetime
import sys

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
    try:
        with open(LICENCE_PATH) as f:
            lic = json.load(f)

        signature = lic.pop("signature")

        if not verify_signature(lic, signature):
            print("❌ Invalid licence signature")
            sys.exit(1)

        if lic["hwid"] != get_hwid():
            print("❌ HWID mismatch")
            sys.exit(1)

        exp = datetime.strptime(lic["expires"], "%Y-%m-%d").date()
        if exp < datetime.now().date():
            print("❌ Licence expired")
            sys.exit(1)

        print("✅ Licence valid")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Licence check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_licence()