from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from rest_framework import permissions

class OrganizationActivePermission(BasePermission):
    message = "Sizning tashkilotingiz faol emas yoki obuna muddati tugagan!"

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if getattr(user, "role", None) == "superadmin":
            return True

        org = getattr(user, "organization", None)
        if not org:
            raise AuthenticationFailed("Tashkilot biriktirilmagan!")
        if not org.is_active:
            raise AuthenticationFailed("Tashkilot faol emas!")
        if org.expiration_date and org.expiration_date < timezone.now().date():
            raise AuthenticationFailed("Tashkilotning obuna muddati tugagan!")

        return True
