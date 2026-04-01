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

def check_licence(terminate_on_fail=False):
    try:
        with open(LICENCE_PATH) as f:
            lic = json.load(f)

        signature = lic.pop("signature")

        if not verify_signature(lic, signature):
            print("❌ Invalid licence signature")
            if terminate_on_fail: sys.exit(1)
            return False

        if lic["hwid"] != get_hwid():
            print("❌ HWID mismatch")
            if terminate_on_fail: sys.exit(1)
            return False

        exp = datetime.strptime(lic["expires"], "%Y-%m-%d").date()
        if exp < datetime.now().date():
            print("❌ Licence expired")
            if terminate_on_fail: sys.exit(1)
            return False

        print("✅ Licence valid")
        return True
    except Exception as e:
        print(f"❌ Licence check failed: {e}")
        if terminate_on_fail: sys.exit(1)
        return False

if __name__ == "__main__":
    ok = check_licence()
    if not ok:
        sys.exit(1)