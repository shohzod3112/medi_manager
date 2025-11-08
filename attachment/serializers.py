from rest_framework import serializers
from .models import Attachment

class AttachmentSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ["id", "name", "file"]

    def get_file(self, obj):
        request = self.context.get("request")
        if obj.file:
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        return None
