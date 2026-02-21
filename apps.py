from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from core.license import get_hwid
        get_hwid()
