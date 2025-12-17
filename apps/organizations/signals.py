import os
from django.conf import settings

from apps.organizations.models import File, Device

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, time
from .models import Organization
from .tasks import deactivate_organization
from celery.result import AsyncResult


@receiver(post_save, sender=Device)
def device_created(sender, instance, created, **kwargs):
    if not created:
        return

    Organization.objects.filter(pk=instance.organization_id).update(
        current_device_count=Device.objects.filter(
            organization_id=instance.organization_id
        ).count()
    )


@receiver(post_delete, sender=Device)
def device_deleted(sender, instance, **kwargs):
    Organization.objects.filter(pk=instance.organization_id).update(
        current_device_count=Device.objects.filter(
            organization_id=instance.organization_id
        ).count()
    )


@receiver(post_save, sender=Organization)
def schedule_expiration_date(sender, instance, created, **kwargs):
    if not instance.expiration_date:
        return

    # eski taskni bekor qil
    if instance.expiration_task_id:
        AsyncResult(instance.expiration_task_id).revoke(terminate=True)

    run_at = datetime.combine(instance.expiration_date, time(23, 59, 59))
    run_at = timezone.make_aware(run_at)

    result = deactivate_organization.apply_async(
        args=[instance.id],
        eta=run_at
    )

    # yangi task ID ni saqlash
    Organization.objects.filter(pk=instance.pk).update(
        expiration_task_id=result.id
    )


@receiver(post_save, sender=File)
def generate_video_preview(sender, instance, **kwargs):


    if instance.type != "video":
        return

    preview_path = os.path.join(
        settings.MEDIA_ROOT,
        "previews",
        f"media_{instance.file_id}.jpg",
    )

    if os.path.exists(preview_path):
        return

    os.makedirs(os.path.dirname(preview_path), exist_ok=True)

    # try:
    #     (
    #         ffmpeg
    #         .input(instance.file.path, ss=1)
    #         .output(preview_path, vframes=1)
    #         .run(capture_stdout=True, capture_stderr=True)
    #     )
    # except ffmpeg.Error as e:
    #     print("FFmpeg error:", e.stderr.decode())
