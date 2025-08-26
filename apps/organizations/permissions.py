from rest_framework.permissions import BasePermission


class IsOrgAndProfileActive(BasePermission):
    message = "User profile or organization is inactive or expired, or user is not assigned to an organization."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            self.message = "Authentication required."
            return False
        profile = getattr(user, "profile", None)
        if not profile or not profile.organization:
            self.message = "User is not assigned to any organization."
            return False
        # Check profile status
        if not profile.is_active or profile.is_expired():
            self.message = "User profile is inactive or expired."
            return False
        # Check organization status
        org = profile.organization
        if not org.is_active or org.is_expired():
            self.message = "Organization is inactive or expired."
            return False
        return True
