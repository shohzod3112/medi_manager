from django.contrib import admin

from attachment.models import Attachment


# Register your models here.
@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'file')