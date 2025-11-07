import time, uuid, hmac, hashlib, base64, requests, os

TOKEN = os.getenv("SWITCHBOT_TOKEN", "YOUR_SWITCHBOT_TOKEN")
SECRET = os.getenv("YOUR_SWITCHBOT_SECRET", "YOUR_SWITCHBOT_SECRET")
BASE = "https://api.switch-bot.com/v1.1"

def headers():
    t = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    payload = (TOKEN + t + nonce).encode("utf-8")
    sign = base64.b64encode(
        hmac.new(SECRET.encode("utf-8"), payload, digestmod=hashlib.sha256).digest()
    ).decode("utf-8").upper()
    return {
        "Authorization": TOKEN,
        "sign": sign,
        "nonce": nonce,
        "t": t,
        "Content-Type": "application/json; charset=utf8"
    }

def get_devices():
    r = requests.get(f"{BASE}/devices", headers=headers())
    return r.json()

if __name__ == "__main__":
    print(f"TOKEN: {TOKEN[:10]}...")
    print(f"SECRET: {SECRET[:10]}...")
    devices = get_devices()
    print("\nデバイス一覧:")
    print(devices)
