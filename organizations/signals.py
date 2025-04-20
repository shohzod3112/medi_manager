import os
import shutil
import ffmpeg

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.conf import settings

from organizations.models import Media


@receiver(post_delete, sender=Media)
def delete_empty_folder(sender, instance, **kwargs):
    """Delete the file's folder if empty, then check and delete the user's folder."""
    if not instance.file:
        return

    file_path = instance.file.path
    folder_path = os.path.dirname(file_path)
    user_folder = os.path.dirname(folder_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    if os.path.exists(folder_path) and not os.listdir(folder_path):
        shutil.rmtree(folder_path)

    if os.path.exists(user_folder) and not os.listdir(user_folder):
        shutil.rmtree(user_folder)


@receiver(post_save, sender=Media)
def generate_video_preview(sender, instance, **kwargs):
    if instance.type != 'video':
        return

    preview_path = os.path.join(settings.MEDIA_ROOT, 'previews', f'media_{instance.media_id}.jpg')

    if os.path.exists(preview_path):
        return

    os.makedirs(os.path.dirname(preview_path), exist_ok=True)

    try:
        (
            ffmpeg
            .input(instance.file.path, ss=1)
            .output(preview_path, vframes=1)
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode())

