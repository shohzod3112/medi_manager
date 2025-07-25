
from rest_framework import serializers

from apps.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser')


# class OrganizationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Organization
#         fields = '__all__'
