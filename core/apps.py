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

        # Server ishga tushayotganini tekshirish (Django autoreload bilan ikki marta ishga tushmasligi uchun)
        import os
        if os.environ.get('RUN_MAIN') == 'true':
            return

        try:
            # Haqiqiy lokal IP-ni aniqlash
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()

            desc = {'version': '1.0.0', 'platform': 'Media-Manager'}

            # Xizmat ma'lumotlari
            info = ServiceInfo(
                "_http._tcp.local.",
                "MediaManagerServer._http._tcp.local.",
                addresses=[socket.inet_aton(ip_address)],
                port=8000,
                properties=desc,
                server="media-server.local.",
            )

            self.zc = Zeroconf()
            self.zc.register_service(info)
            print(f"✅ Zeroconf: Server ro'yxatga olindi: {ip_address}:8000")
        except Exception as e:
            print(f"❌ Zeroconf xatosi: {e}")
            traceback.print_exc()

    def __del__(self):
        # Konteyner o'chganda xizmatni tozalash
        if hasattr(self, 'zc'):
            self.zc.close()