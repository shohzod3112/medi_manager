from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone


class CustomAdminAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        # 1️⃣ Organization tekshirish
        if not user.organization:
            raise ValidationError(
                "Sizning profilingizga tashkilot biriktirilmagan!",
                code='invalid_login'
            )

        # 2️⃣ Tashkilot active bo‘lishi shart
        if not user.organization.is_active:
            raise ValidationError(
                "Sizning tashkilotingiz faol emas!",
                code='invalid_login'
            )

        # 3️⃣ Obuna muddati tugaganmi?
        if user.organization.expiration_date < timezone.now().date():
            raise ValidationError(
                "Sizning obuna muddatingiz tugagan!",
                code='invalid_login'
            )

        # 4️⃣ Staff bo‘lmasa
        if not user.is_staff:
            raise ValidationError("Sizda admin panelga kirish ruxsati yo‘q!")


admin.site.login_form = CustomAdminAuthenticationForm
