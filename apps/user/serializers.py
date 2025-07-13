# user/serializers.py
from rest_framework import serializers
from .models import User, Organization

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser', 'organization_db_name')

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = '__all__'
