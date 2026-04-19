import socket
import json
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'UDP Discovery xizmati (9999 port)'

    def get_server_ip(self):
        """Serverning haqiqiy tarmoq IP manzilini dinamik aniqlaydi"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Haqiqiy tarmoq interfeysini aniqlash uchun tashqi manzilga 'ulanish'
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def handle(self, *args, **options):
        # UDP socket yaratish
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Portni band qilishda xatolik bo'lmasligi uchun REUSEADDR qo'shamiz
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 9999 portni hamma interfeyslarda tinglaymiz
        sock.bind(('', 9999))

        self.stdout.write(self.style.SUCCESS("📡 UDP Discovery xizmati 9999-portda ishga tushdi..."))

        while True:
            try:
                # Paket qabul qilish
                data, addr = sock.recvfrom(1024)

                # Ma'lumotni dekodlash (xatolarga chidamli holatda)
                try:
                    message = data.decode('utf-8', errors='ignore')
                except:
                    message = str(data)

                # "DISCOVER" so'zi xabar ichida bormi (JSON bo'lsa ham topadi)
                if "DISCOVER" in message.upper():
                    real_ip = self.get_server_ip()

                    self.stdout.write(self.style.SUCCESS(f"✅ So'rov keldi! Kimdan: {addr[0]}"))
                    self.stdout.write(f"ℹ️ Xabar tarkibi: {message}")

                    response_data = {
                        "status": "online",
                        "server_name": "Media-Manager-Server",
                        "server_ip": real_ip,
                        "port": 8000
                    }

                    # Javob yuborish
                    response = json.dumps(response_data).encode('utf-8')
                    sock.sendto(response, addr)

                    self.stdout.write(f"🚀 Javob yuborildi: {real_ip}:8000")
                else:
                    self.stdout.write(f"⚠️ Noma'lum paket keldi: {message} | Kimdan: {addr