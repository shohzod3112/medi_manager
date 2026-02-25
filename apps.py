from django.apps import AppConfig
from core.licence import check_license

class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        check_license()