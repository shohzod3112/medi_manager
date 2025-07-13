from django.apps import AppConfig

class OrganizationsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organizations'

    def ready(self):
        import organizations.signals  # Import the signals
