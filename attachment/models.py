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

    class Meta:
        db_table = 'attachments'
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"
