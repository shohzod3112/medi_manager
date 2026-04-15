import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

# 1. GENERATSIYA QILGAN PRIVATE KEYINGIZNI SHU YERGA QO'YING
# (O'sha uzun, -----BEGIN PRIVATE KEY----- bilan boshlanadigan matn)
private_key_pem = """-----BEGIN PRIVATE KEY-----
MIIEugIBADANBgkqhkiG9w0BAQEFAASCBKQwggSgAgEAAoIBAQCo6A9J0uklpM5n
ejgPhRoLIsG/CQt4LbCTJxgLh942BknmGC/avwV5W9cSR1hnE54y1Cvar/Cw9msL
J6S7zmD9OMI55UJ7USOTRlrf233dv+nIpZf69C5hBZ1OcRXRS80i4lHoixy6myiP
9bGqtJVyUHEgkGHu/ZN4KLGnAH+yNmZANiu9oC5jBI+y1MI0ChRAjSSzTLIC7kfn
QIny62Bi9JFWr7j1w4+/iigU/PHwRqjx+9MSPlj4hcF/DoEcJF8wH9L/7rvZ/Nq6
2Gb1+RdwTjYFtwsj08M5vb+6kCu5HESFzK5k4y0elzX23MPh52Vx4w+//2BJ22kL
+wrVuh3vAgMBAAECgf9N5rm4rjJsF/I/EJ+BZGIenCAI6X5zAXsTiAahStH7GMbX
/U/LyrwXBg3QTheKBSbfSo5dF39GsTutjfajOjDKmXVEPosPnkpKIqjHBBk/9jE4
a7m/FwRNBFwtmrFjDVwPX1KMSZzkKtAvAxAlK0kvy3xhmsgiqKzbPnvVwS5Ip1dI
v7CoZLtQ/6BENLlanhpzDP5Y+C/9MAEp6j2YJ50Dpymg35pp77a/VyrqGN+xPkjP
LuSVYLcmkEEueZX05w9zrC0KCVIshoiszvi27vlY5E1JbvQxMXFRfmLMoTlFe3Ki
61f4PmtsNUNn+SQvYXnPTndx+hAUP0RWdQsCtrUCgYEA3fivQD+2e2Aj2HSyNdQL
bGtogxJEwPxkGOxHKQiVlhaebvpby6HfJstu4SfztUFMEfQ9wDt1X8EHKmXsUAl+
e0GM2BtaUMxWSY87q4mdtYArEfQ8n9C1rDqgYGDIbrJD6Ok3SciInDUSVfDC0fIZ
wFgCx7KL1NT79/GAIZUHDM0CgYEAwszUkMknRHGTQDFV1LljaeTqXnsrBWdLeaP0
8J1ILQxq0CJUC15+Eul1IYOdcS0ZTe7x+y9nOM6B5J8QHJ+a25MpFOqft5FQKebh
y8oas+ADEbdMXZQnZkPcMaXxMYxcc4OgvebPu5rgxjkBX2V03YZyf7l6zmTeYb4A
W53W1asCgYAwQCyoRLFAJGfmV4edl9hb2wU+6Ku1X6fKmyHk047gr04FRbrKiwdd
AX+6xdp+HhGRHYyGyuX6yJTsLHev9kBePqOFHn0Fb0Wae942rZVwrMmv/21mOBIl
vCC8ko0/MtT8PiXcjhDUE91GfS18QapDW15PVop620liXkbCBgkgSQKBgFVUrHiP
5OeSaNJhyhtY6jdk01V31qyTRviN3anY+9jf65oor3AbgFaAdZKsuLbu7nq5BL7n
UOwNadDf7IrdT1SH7iL/c99RhDAWtyox6eiJZE7KYGVNlMSzTS1iZ3kw5v6i1jLZ
fH3NplCuf+9t3fd8AYP5l9X5UYC3XijDx2vpAoGAEz7Lh0Vr8ucCq1U7ZlsNIpeg
c1CyPiyK3hxj0j8Mq9DPt8wzTpPcO34gH7fE0vnVpSwo8s9Z7qeSftW0n/H2EAV6
4cVFYHZW065PMk4FyDtrR65NwWvyhDZcaxKnOCzEtfl4AmGTSxQZxlN7S6Fg9Jdz
ARdiYmG7EQaAxiLJG+E=
-----END PRIVATE KEY-----"""

# 2. Kalitni yuklash
priv_key = serialization.load_pem_private_key(
    private_key_pem.encode(),
    password=None
)

# 3. ABC123 ni imzolash
device_id = "ABC123"
signature = priv_key.sign(
    device_id.encode(),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# 4. Natijani Base64 ko'rinishida chiqarish (Curl uchun)
print("\n--- HAQIQIY IMZO (SIGNATURE) ---\n")
print(base64.b64encode(signature).decode())
print("\n-------------------------------\n")