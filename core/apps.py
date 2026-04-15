import traceback
from django.apps import AppConfig
import socket
from zeroconf import ServiceInfo, Zeroconf

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "core"

    def ready(self):
        from .check_licence import check_licence
        check_licence()
