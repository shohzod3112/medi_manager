import socket
import json
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'UDP Discovery xizmatini ishga tushiradi (9999 port)'

    def handle(self, *args, **options):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 9999))

        # Muhim: Bu soketga javob qaytarish huquqini beramiz
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.stdout.write(self.style.SUCCESS("📡 UDP Discovery xizmati ishga tushdi..."))

        while True:
            try:
                data, addr = sock.recvfrom(1024)

                # Decodingni ehtiyotkorlik bilan qilamiz
                try:
                    message = data.decode('utf-8', errors='ignore')
                except:
                    message = str(data)

                # "DISCOVER" so'zi xabar ichida bormi (JSON ichida bo'lsa ham topadi)
                if "DISCOVER" in message.upper():
                    self.stdout.write(f"✅ So'rov keldi. IP: {addr[0]} | Xabar: {message}")

                    response_data = {
                        "status": "online",
                        "server_name": "Media-Manager-Server",
                        "server_ip": "10.170.1.10",  # Qo'lda yozish aniqroq (Temporary)
                        "port": 8000
                    }

                    response = json.dumps(response_data).encode('utf-8')
                    sock.sendto(response, addr)
                else:
                    self.stdout.write(f"ℹ️ Boshqa paket keldi: {message}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Xato: {str(e)}"))