import socket
import json
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'UDP Discovery xizmatini ishga tushiradi (9999 port)'

    def handle(self, *args, **options):
        # UDP socket yaratamiz
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 9999 portni hamma interfeyslarda tinglaymiz
        sock.bind(('', 9999))

        self.stdout.write(self.style.SUCCESS("📡 UDP Discovery xizmati 9999-portda ishga tushdi..."))

        while True:
            try:
                # Paket kutamiz
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8')

                if "DISCOVER" in message:
                    # Server o'z IP-sini aniqlaydi (ixtiyoriy, lekin foydali)
                    server_ip = socket.gethostbyname(socket.gethostname())

                    response_data = {
                        "status": "online",
                        "server_name": "Media-Manager-Server",
                        "server_ip": server_ip,  # <-- IP-ni matn qilib qo'shdik
                        "port": 8000
                    }

                    response = json.dumps(response_data).encode('utf-8')
                    sock.sendto(response, addr)

                    self.stdout.write(f"✅ Discovery so'rovi keldi: {addr[0]}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Xato: {str(e)}"))