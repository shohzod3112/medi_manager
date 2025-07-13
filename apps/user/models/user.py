from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now  # ✅ Correct import


def get_default_expiration_date():
    return now().date()  # ✅ Ensure it returns only a date


# class Organization(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     db_name = models.CharField(max_length=255, unique=True)
#
#     def __str__(self):
#         return self.name


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(blank=False, unique=True)
    is_superuser = models.BooleanField(default=False)
    # organization = models.ForeignKey(
    #     Organization,
    #     on_delete=models.CASCADE,
    #     related_name="users",
    #     null=True,
    #     blank=False
    # )
    device_limit = models.PositiveIntegerField(default=5)
    expiration_date = models.DateField(null=True, blank=False)  # ✅ Fixed

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username
