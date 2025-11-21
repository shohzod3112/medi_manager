import os

from django.db import models

class Attachment(models.Model):
    name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
    )
    file = models.FileField(upload_to='attachments/')

    def __str__(self):
        return self.name


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
