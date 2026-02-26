import json, hmac, hashlib, sys
from hwid import generate_hwid
from datetime import date

SECRET = b"LOCAL_MEDIA_MANAGER_SECRET"
LICENCE_FILE = "/licence/licence.json"

def _verify(data):
    sig = data.pop("signature", None)
    raw = json.dumps(data, sort_keys=True).encode()
    exp = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    return sig and hmac.compare_digest(sig, exp)

def check_or_exit():
    try:
        lic = json.load(open(LICENCE_FILE))
    except Exception:
        print("❌ Licence not found")
        sys.exit(1)

    if lic.get("hwid") != generate_hwid():
        print("❌ HWID mismatch")
        sys.exit(1)

    if not _verify(dict(lic)):
        print("❌ Invalid licence signature")
        sys.exit(1)

    if "expires" in lic:
        if date.fromisoformat(lic["expires"]) < date.today():
            print("❌ Licence expired")
            sys.exit(1)

    print("✅ Licence OK")