import sounddevice as sd
import numpy as np
import time
import requests
import os
import hmac
import hashlib
import base64
import uuid

CANDIDATE_RATES = [48000, 44100]  # ← この順で試す
BLOCK = 1024
DB_THRESH = -100
BAND = (800, 2000)

# SwitchBot API設定
SWITCHBOT_TOKEN = os.getenv('SWITCHBOT_TOKEN')
SWITCHBOT_SECRET = os.getenv('YOUR_SWITCHBOT_SECRET')
SWITCHBOT_DEVICE_ID_1 = os.getenv('SWITCHBOT_DEVICE_ID_1')
SWITCHBOT_DEVICE_ID_2 = os.getenv('SWITCHBOT_DEVICE_ID_2')
SWITCHBOT_API_BASE = 'https://api.switch-bot.com/v1.1'

# 環境変数チェック
if not SWITCHBOT_TOKEN:
    print("⚠️ 警告: SWITCHBOT_TOKEN が設定されていません")
if not SWITCHBOT_SECRET:
    print("⚠️ 警告: YOUR_SWITCHBOT_SECRET が設定されていません")
if not SWITCHBOT_DEVICE_ID_1 and not SWITCHBOT_DEVICE_ID_2:
    print("⚠️ 警告: デバイスIDが設定されていません")

# オーディオデバイスの設定（デフォルトデバイスを使用）
# sd.default.device = ("USB デバイスが見つからないです", None)

def pick_working_rate():
    print("利用可能なオーディオデバイス:")
    print(sd.query_devices())
    print("\nデフォルトデバイス:", sd.default.device)

    for r in CANDIDATE_RATES:
        try:
            with sd.InputStream(channels=1, samplerate=r, blocksize=BLOCK, dtype='float32'):
                print(f"✅ サンプルレート {r}Hz が使用可能です")
                return r
        except Exception as e:
            print(f"⚠️ サンプルレート {r}Hz でエラー: {e}")
    raise RuntimeError("No supported sample rate found. 利用可能なオーディオデバイスを確認してください。")

RATE = pick_working_rate()
sd.default.samplerate = RATE
print(f"Using samplerate: {RATE}")

def dbfs(x):
    rms = np.sqrt(np.mean(x**2) + 1e-12)
    return 20*np.log10(rms + 1e-12)

def bandpower(x, rate, f_lo, f_hi):
    X = np.fft.rfft(x * np.hanning(len(x)))
    freqs = np.fft.rfftfreq(len(x), 1/rate)
    band = (freqs >= f_lo) & (freqs <= f_hi)
    p = np.mean(np.abs(X[band])**2)
    return 10*np.log10(p + 1e-12)

def generate_sign(token, secret, nonce, t):
    """SwitchBot API v1.1の署名を生成"""
    string_to_sign = bytes(f"{token}{t}{nonce}", 'utf-8')
    secret_bytes = bytes(secret, 'utf-8')
    sign = base64.b64encode(
        hmac.new(secret_bytes, msg=string_to_sign, digestmod=hashlib.sha256).digest()
    ).decode('utf-8')
    return sign

def call_switchbot_api(device_id, command, parameter="default", command_type="command"):
    """
    SwitchBot APIを呼び出してデバイスを制御する (v1.1対応)

    Args:
        device_id: デバイスID
        command: コマンド名 (turnOn, turnOff, press など)
        parameter: コマンドパラメータ (デフォルト: "default")
        command_type: コマンドタイプ (デフォルト: "command")

    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    url = f"{SWITCHBOT_API_BASE}/devices/{device_id}/commands"

    # v1.1認証ヘッダーの生成
    t = str(int(time.time() * 1000))
    nonce = str(uuid.uuid4())
    sign = generate_sign(SWITCHBOT_TOKEN, SWITCHBOT_SECRET, nonce, t)

    headers = {
        "Authorization": SWITCHBOT_TOKEN,
        "sign": sign,
        "nonce": nonce,
        "t": t,
        "Content-Type": "application/json; charset=utf8"
    }
    payload = {
        "command": command,
        "parameter": parameter,
        "commandType": command_type
    }

    try:
        print(f"🔄 API呼び出し: {device_id} - {command}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"📡 レスポンスステータス: {response.status_code}")
        result = response.json()
        print(f"📄 レスポンス内容: {result}")

        response.raise_for_status()

        if result.get('statusCode') == 100:
            print(f"✅ SwitchBot API成功: {command}")
            return True
        else:
            print(f"⚠️ SwitchBot API警告: statusCode={result.get('statusCode')}, message={result.get('message', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ SwitchBot API エラー: {e}")
        return False

def on_chime_detected():
    print("🔔 音を感知しました！！")
    # SwitchBotのスイッチをONにする
    if SWITCHBOT_DEVICE_ID_1:
        call_switchbot_api(SWITCHBOT_DEVICE_ID_1, "turnOn")
        call_switchbot_api(SWITCHBOT_DEVICE_ID_2, "turnOn")



with sd.InputStream(channels=1, samplerate=RATE, blocksize=BLOCK, dtype='float32') as stream:
    cool_down = 0
    print("Listening...")
    while True:
        data, _ = stream.read(BLOCK)
        x = data[:,0]
        vol = dbfs(x)
        bp = bandpower(x, RATE, *BAND)
        if vol > DB_THRESH and bp > -20 and cool_down <= 0:
            on_chime_detected()
            cool_down = int(RATE / BLOCK * 3)
        cool_down = max(0, cool_down-1)
        time.sleep(0.005)