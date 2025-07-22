
from rest_framework import serializers



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser', 'organization_db_name')


# class OrganizationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Organization
#         fields = '__all__'
