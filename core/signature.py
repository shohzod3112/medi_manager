import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from django.conf import settings

# 1. Qurilmaning PRIVATE KEY'i (Buni o'zingizda generatsiya qilganingiz deb hisoblaymiz)
# Agar yo'q bo'lsa, avvalgi generate_server_keys funksiyasidan foydalaning
private_key_pem = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCimhpek7kxHG03
YUVElix7Lff9Oj2NDgiZh+H3WfgRYjqdPeTQv5d6CKO0bvnbmlGgkqjEGVZMaq3h
XjRmo9HUr95Rbnm2A7jH7C7VulA3HIW7R2n7fix0YxkDlUn6+/5Dhazx0aXw+idx
WgIMGML4K+ueMo1XrScGh5oqVRwpg9v31BIIlbDTPHhJzE+Bfck5FjqCSWZ0nRdw
GjRy4nScMODFt2jNgaXP9f4YW1WKV2ZJSy11upwlmUw7QT+ICUVfNFs+I440JI20
r9+gi7RD16gtEhj/Teu8HDnXm7iZV30bIFIw37Dt+Gzf5J4BzPlOQOmOQ0xpIpwr
yGDb4svtAgMBAAECggEADzmfu3hYkFUpktRsUHpBSv1oaZEg/0qvmnSjP25wsGwC
sgOAH924uMgDUBtOEPZ3qzHgVJBMyNX6Vw5jmLLBLImVJwnRoq3hiPLABeoupaJp
kTokHdTYI8O9rVy2syYSTk8/fNsVDyXVOKNlaq2M4AD4zHTOUEXZ0B41XL5gZzCX
tO5abIgDmMH8hoae5G5wZ3W2u2PPm0ehCUXATO6JsPbGexDS5V8z8vzqaSEN3V5Z
stlL/Aw/bWe504StWrOFKLcWTEyGg6kauu+Wx1ly/1YAD2OlWS9M7NNgkiTIKBX2
qnpOSx2hPQR2mC6YjiBq8ug4wmh/PW48QwXtn6pNkQKBgQDfNgizNRS5CEqyRigb
dXgl9PBWb8wWOw9y7Vwfnvewav93a8aM+k1tB4HdibYmS6jppwvw5ummlDTkisPz
3+0Mm/KU6YrXqOuY2UohJnKvJayRLKuNe4E6zaVEqQ1xayZs72Ny9BUMUPM+37TK
Rt0zCFSG4bapuB4Bi52RSmdqSQKBgQC6fNUuGtfsRHGFlLVPmWj0DnkxZDZkxFZ/
6FrFA7DAwBkXrMd/Tt8lcF9gfM/8r7TYki+ZctW8qKSz+w86nr/4FzQMkRgrCE7H
giEcEquZ5EkGzIQiOgliugNXfQ22d7bB7pS6d3h3J+kZXYWhWNFmpJLPkocaDGwY
6jVBRAP0hQKBgEgfdYAyTpfbDge8k4kL096v3liPlyo3uy4vc+zjuLTQXeuAb49t
8UahflzO+oQ1PkcBKuKUOjsQ+GZAUECkwjuoyCFFtQ8qDbY9v64mdjgRvEjMXkJA
/ei6OgSNe0KClM/uKfwi0gpAvdg7AHe7ng23S1ip5hPA4jEto6QmnnPBAoGALRfY
WICnK3tVU+6kdO3sge8qAPZxbKZJID6oDDGbQNBygNYHm1IQBTaJ6YPkqv41pZSb
q+gnpKnGwbp4cT1HwA6kSFGhXW5x1i4yIV6mXdzkh59WaAxOjq/Z9QLJGRETgQtW
rUwMNgvRgo+pq10VrVMoKMcOog7U6KVhYTm4Fx0CgYBwCZWANsSkTtXOD+/fAC7w
qfFysa1PmnwThQJDWQM8k+7qlf1S3YbIaJenMSolvetxHJ1o3XlH9CLLgimK4rky
OACSh3oWtqjmdApras75n6yJQ7Ete0/SVMi5VmhJmv1l4Y38QBw5TFjoharh667p
5vNiuTjlinu2di+LqPKE9g==
-----END PRIVATE KEY-----"""

priv_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)

# 2. device_id ni imzolash
device_id = "ABC123"
signature = priv_key.sign(
    device_id.encode(),
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

print(base64.b64encode(signature).decode())