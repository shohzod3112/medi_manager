from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.organizations.models import Organization
import logging

logger = logging.getLogger("app")
User = get_user_model()

@shared_task
def log_order_created(user_id):
    try:
        user = User.objects.get(id=user_id)
        logger.info("order created", extra={
            "user": user.id,
            "method": "CELERY",
            "path": "create_order_task",
            "status": "OK",
        })
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found, could not log order creation")

@shared_task
def disable_expired_staff():
    now = timezone.now()
    organizations = Organization.objects.filter(
        is_active=True,
        expiration_date__isnull=False,
        expiration_date__lt=now,
    )
    if organizations.exists():
        organizations.update(is_active=False)

@shared_task
def deactivate_organization(org_id):
    try:
        org = Organization.objects.get(id=org_id)
        org.is_active = False
        org.save()
    except Organization.DoesNotExist:
        pass
