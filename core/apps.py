from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from .check_licence import check_licence
        check_licence()