import json, sys, hashlib

def get_hwid():
    try:
        with open("/licence/licence.json") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit("Licence file not found!")

    try:
        with open("/etc/machine-id") as f:
            hwid = hashlib.sha256(f.read().encode()).hexdigest()
    except:
        hwid = "unknown"

    if data.get("hwid") != hwid:
        sys.exit("Licence HWID mismatch!")
