import os
import shutil
from django.db.models.signals import post_delete
from django.dispatch import receiver
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
