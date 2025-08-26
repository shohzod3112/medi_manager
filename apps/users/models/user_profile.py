from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now


class UserProfile(models.Model):
    """
    UserProfile model that extends the User model with organization-specific fields.
    This handles the relationship between users and organizations.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="user_profiles",
    )
    device_limit = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Maximum number of devices this users can have",
    )
    current_device_count = models.PositiveIntegerField(
        default=0,
        help_text="Current number of devices assigned to this users",
    )
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text="User subscription expiration date",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this users profile is active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "users"
        db_table = "user_profiles"
        verbose_name_plural = "User Profiles"
        verbose_name = "User Profile"
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} - {self.organization.name}"

    def clean(self):
        """Validate that users device limit doesn't exceed organization limit"""
        if self.organization and self.device_limit:
            if self.pk:  # Existing instance
                old_instance = UserProfile.objects.get(pk=self.pk)
                old_limit = old_instance.device_limit
            else:
                old_limit = 0

            # Calculate the change in device limit
            limit_change = self.device_limit - old_limit

            # Check if organization has enough capacity
            org_used_devices = self.organization.get_total_used_devices()
            org_available = (
                self.organization.device_limit - org_used_devices + old_limit
            )

            if limit_change > org_available:
                raise ValidationError(
                    {
                        "device_limit": f'Organization "{self.organization.name}" only has {org_available} device slots available. '
                        f"Cannot assign {self.device_limit} devices to this users.",
                    },
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def can_add_device(self):
        """Check if users can add another device"""
        return self.current_device_count < self.device_limit

    def add_device(self):
        """Increment device count"""
        if self.can_add_device():
            self.current_device_count += 1
            self.save(update_fields=["current_device_count"])
            return True
        return False

    def remove_device(self):
        """Decrement device count"""
        if self.current_device_count > 0:
            self.current_device_count -= 1
            self.save(update_fields=["current_device_count"])
            return True
        return False

    def get_remaining_devices(self):
        """Get remaining device slots"""
        return self.device_limit - self.current_device_count

    def is_expired(self):
        """Check if users subscription is expired"""
        if self.expiration_date:
            return self.expiration_date < now().date()
        return False
