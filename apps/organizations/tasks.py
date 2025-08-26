from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


@shared_task
def disable_expired_staff():
    """
    Disable expired staff users.
    """
    now = timezone.now()
    expired_users = User.objects.filter(
        is_staff=True,
        expiration_date__isnull=False,
        expiration_date__lt=now,
    )

    if expired_users.exists():
        expired_users.update(is_staff=False)
