from rest_framework.permissions import BasePermission


class IsOrgAndProfileActive(BasePermission):
    message = "User profile or organization is inactive or expired, or user is not assigned to an organization."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            self.message = "Authentication required."
            return False
        if not user.organization:
            self.message = "User is not assigned to any organization."
            return False
        # Check organization status
        org = user.organization
        if not org.is_active or org.is_expired():
            self.message = "Organization is inactive or expired."
            return False
        return True
