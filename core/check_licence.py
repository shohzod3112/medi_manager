import json
import hmac
import hashlib
from datetime import datetime
import sys
import os

SECRET = b"LOCAL_MEDIA_MANAGER_SECRET"
LICENCE_PATH = "/opt/media-manager/licence/licence.json"
# Vaqtni saqlash uchun maxsus fayl (Volume ichida)
TIME_TRACKER_PATH = "/opt/media-manager/licence/last_run.json"


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
        now = datetime.now()

        # --- VAQTNI ORQAGA QAYTARISH TEKSHIRUVI --- [cite: 18, 19, 21]
        if os.path.exists(TIME_TRACKER_PATH):
            with open(TIME_TRACKER_PATH, "r") as tf:
                time_data = json.load(tf)
                last_run = datetime.fromisoformat(time_data["last_run"])

                if now < last_run:
                    print("❌ ERROR: Server time has been rolled back!")
                    if terminate_on_fail: sys.exit(1)
                    return False

        # --- LITSENZIYA TEKSHIRUVI --- [cite: 133]
        if not os.path.exists(LICENCE_PATH):
            print("❌ Licence file missing")
            if terminate_on_fail: sys.exit(1)
            return False

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

        exp = datetime.strptime(lic["expires"], "%Y-%m-%d")
        if exp < now:
            print("❌ Licence expired")
            if terminate_on_fail: sys.exit(1)
            return False

        # --- VAQTNI YANGILASH --- [cite: 20, 48]
        with open(TIME_TRACKER_PATH, "w") as tf:
            json.dump({"last_run": now.isoformat()}, tf)

        print("✅ Licence and Time valid")
        return True
    except Exception as e:
        print(f"❌ Licence check failed: {e}")
        if terminate_on_fail: sys.exit(1)
        return False


if __name__ == "__main__":
    check_licence(terminate_on_fail=True)