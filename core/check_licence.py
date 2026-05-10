import json
import hmac
import hashlib
import sys
import os

from datetime import datetime, timedelta

# Django muhitini tekshirish
try:
    from django.utils import timezone

    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

SECRET = b"LOCAL_MEDIA_MANAGER_SECRET"
LICENCE_PATH = "/opt/media-manager/licence/licence.json"
TIME_TRACKER_PATH = "/opt/media-manager/licence/last_run.json"


def verify_signature(data, signature):
    raw = json.dumps(data, sort_keys=True).encode()
    expected = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def get_hwid():
    try:
        with open("/etc/machine-id") as f:
            mid = f.read().strip()
        return hashlib.sha256(mid.encode()).hexdigest()
    except:
        return "unknown-hwid"


def check_consensus_time():
    """Qurilmalar konsensusini tekshirish - faqat Django ichida ishlaydi"""
    if not HAS_DJANGO:
        return True  # Build vaqtida (hostda) bu tekshiruv o'tkazib yuboriladi

    try:
        # DIQQAT: Importni funksiya ichiga ko'chirdik (Lazy Import)
        from attachment.models import DeviceTimeReport

        reports = DeviceTimeReport.objects.all()
        total_devices = reports.count()

        if total_devices < 5:
            return True

        now = timezone.now()
        outdated_count = 0
        threshold = timedelta(hours=24)

        for report in reports:
            # Agar qurilma vaqti serverdan 24 soatdan ko'p oldinda bo'lsa
            if report.last_reported_time > (now + threshold):
                outdated_count += 1

        # 80% dan oshsa (ya'ni 20% gacha ruxsat bor)
        if (outdated_count / total_devices) >= 0.8:
            print("❌ CRITICAL: 80% devices report that server time is fake (too old)!")
            return False

        return True
    except Exception as e:
        # Bazaga ulanib bo'lmasa yoki model topilmasa ham build to'xtamasligi kerak
        return True


def check_licence(terminate_on_fail=False):
    try:
        now = datetime.now()

        # 1. VAQTNI ORQAGA QAYTARISH TEKSHIRUVI
        if os.path.exists(TIME_TRACKER_PATH):
            with open(TIME_TRACKER_PATH, "r") as tf:
                time_data = json.load(tf)
                last_run = datetime.fromisoformat(time_data["last_run"])

                if now < (last_run - timedelta(seconds=60)):
                    print(f"❌ ERROR: Server time rollback! Current: {now}, Last: {last_run}")
                    if terminate_on_fail: sys.exit(1)
                    return False

        # 2. LITSENZIYA FAYLI VA HWID TEKSHIRUVI
        if not os.path.exists(LICENCE_PATH):
            print("❌ Licence file missing")
            if terminate_on_fail: sys.exit(1)
            return False

        with open(LICENCE_PATH) as f:
            lic = json.load(f)

        signature = lic.pop("signature", None)
        if not signature or not verify_signature(lic, signature):
            print("❌ Invalid licence signature")
            if terminate_on_fail: sys.exit(1)
            return False

        if lic["hwid"] != get_hwid():
            print("❌ HWID mismatch")
            if terminate_on_fail: sys.exit(1)
            return False

        exp = datetime.strptime(lic["expires"], "%Y-%m-%d")
        if exp < now:
            print(f"❌ Licence expired on {lic['expires']}")
            if terminate_on_fail: sys.exit(1)
            return False

        # 3. QURILMALAR KONSENSUSINI TEKSHIRISH
        if not check_consensus_time():
            if terminate_on_fail: sys.exit(1)
            return False

        # 4. VAQT TREKKERINI YANGILASH
        if not os.path.exists(TIME_TRACKER_PATH) or now > last_run:
            with open(TIME_TRACKER_PATH, "w") as tf:
                json.dump({"last_run": now.isoformat()}, tf)

        print("✅ Licence and Time valid")
        return True
    except Exception as e:
        print(f"❌ Licence check error: {e}")
        if terminate_on_fail: sys.exit(1)
        return False


if __name__ == "__main__":
    check_licence(terminate_on_fail=True)