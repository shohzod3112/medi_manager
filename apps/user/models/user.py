from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now
from django.core.validators import MinValueValidator


def get_default_expiration_date():
    return now().date()


class User(AbstractUser):
    username = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='user_avatars/', blank=True, null=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    class Meta:
        ordering = ['username']
        db_table = 'users'
        verbose_name_plural = 'Users'
        verbose_name = 'User'
