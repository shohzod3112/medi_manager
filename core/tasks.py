from celery import shared_task
from core.check_licence import check_licence
import logging

logger = logging.getLogger(__name__)


@shared_task(name="daily_security_check")
def daily_security_check():
    """
    Har kuni litsenziya va qurilmalar vaqtini tekshiruvchi vazifa
    """
    logger.info("🔍 Starting daily security and consensus check...")

    # terminate_on_fail=False qilamiz, aks holda Celery worker to'xtab qoladi.
    # Buning o'rniga natijaga qarab chora ko'rish mumkin.
    is_valid = check_licence(terminate_on_fail=False)

    if not is_valid:
        logger.error("❌ Security check failed! Taking restrictive actions...")
        # Bu yerda tizimni cheklash mantiqini yozishingiz mumkin
        # Masalan: Cache orqali barcha API'larni yopib qo'yish
    else:
        logger.info("✅ Daily security check passed.")