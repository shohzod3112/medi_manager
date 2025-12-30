import os
import subprocess

from django.db import models


class Attachment(models.Model):
    name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
    )
    file = models.FileField(upload_to='attachments/')
    gif = models.FileField(upload_to='attachments/gifs/', blank=True, null=True)

    def __str__(self):
        return self.name

    def create_gif(self, duration=5, fps=10, width=320):
        """
        Video fayldan GIF yaratish (maks 5 sekund, kichik hajm)
        """
        video_path = self.file.path
        gif_name = os.path.splitext(os.path.basename(video_path))[0] + '.gif'
        gif_path = os.path.join(os.path.dirname(video_path), 'gifs', gif_name)

        # 'gifs' papka borligini tekshiramiz
        os.makedirs(os.path.dirname(gif_path), exist_ok=True)

        # ffmpeg orqali GIF yaratish
        command = [
            'ffmpeg',
            '-ss', '0',  # 0 sekunddan boshlaymiz
            '-t', str(duration),  # davomiylik
            '-i', video_path,  # input video
            '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',  # fps va width
            '-y', gif_path  # output fayl
        ]
        subprocess.run(command, check=True)

        # GIFni modelga bog'laymiz
        relative_gif_path = os.path.relpath(gif_path, os.path.join(os.path.dirname(video_path), '../'))
        self.gif.name = os.path.join('attachments/gifs/', gif_name)
        super().save(update_fields=['gif'])

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if (
                is_new and
                self.file and
                self.file.name.lower().endswith(('.m4v', '.mp4', '.m4p', '.mov', '.qt', '.wmv', '.avi',
                                                 '.mkv', '.webm', '.flv', '.f4v', '.f4p', '.f4a' '.f4b',
                                                 '.3gp', '.3g2', '.mpg', '.mp2', '.mpeg','.mpe', '.mpv',
                                                 '.m2v', '.vob', '.ts', '.mts', '.m2ts', '.ogv', '.ogg',
                                                 '.gifv', '.mng', '.yuv', '.rm', '.rmvb', '.viv', '.asf',
                                                 '.amv', '.svi', '.mxf', '.roq', '.nsv', '.rrc', '.mod')) and
                not self.gif
        ):
            self.create_gif()

    def delete(self, *args, **kwargs):
        # Faylni media papkadan o‘chiramiz
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        # Bazadan yozuvni o‘chiramiz
        super().delete(*args, **kwargs)

    class Meta:
        db_table = 'attachments'
        verbose_name = "File"
        verbose_name_plural = "Files"
