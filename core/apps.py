from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "core"

    def ready(self):
        from .check_licence import check_licence
        from .security import ensure_server_keys
        check_licence()
        ensure_server_keys()
