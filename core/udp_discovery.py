import os
import socket
import json


def start_udp_discovery(server_ip, server_port=8000):
    UDP_IP = "0.0.0.0"  # Barcha interfeyslarni tinglash
    UDP_PORT = 9999

    # Soket yaratish
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"📡 UDP Discovery Server ishga tushdi (Port: {UDP_PORT})...")

    while True:
        # Clientdan ma'lumot kutish
        data, addr = sock.recvfrom(1024)
        try:
            message = json.loads(data.decode())
            if message.get("type") == "DISCOVER":
                print(f"🔍 Discovery so'rov keldi: {addr[0]}")

                # Javob tayyorlash
                response = {
                    "type": "DISCOVER_RESPONSE",
                    "ip": "10.170.100.7",
                    "port": 8000,
                    "pubkey": os.getenv("SERVER_PUBLIC_KEY"),  # Yuqorida yaratilgan PEM formatdagi kalit
                    "name": "media-manager-server"
                }

                # Javobni qaytarib yuborish
                sock.sendto(json.dumps(response).encode(), addr)
        except Exception as e:
            print(f"❌ UDP xatosi: {e}")

# Ishga tushirish (Test uchun):
# start_udp_discovery("10.170.100.7")