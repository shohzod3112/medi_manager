from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.organizations.models import Organization

User = get_user_model()


@shared_task
def disable_expired_staff():
    """
    Disable expired staff users.
    """
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