import os
from django.conf import settings

from apps.organizations.models import File

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime, time
from .models import Organization
from .tasks import deactivate_organization


@receiver(post_save, sender=Organization)
def schedule_expiration_date(sender, instance, created, **kwargs):
    if not created:
        return

    if not instance.expiration_date:
        return

    run_at = datetime.combine(instance.expiration_date, time(23, 59, 59))
    run_at = timezone.make_aware(run_at)

    deactivate_organization.apply_async(
        args=[instance.id],
        eta=run_at
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
