from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        # Licence check is triggered via Django system checks
        pass