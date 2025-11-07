import sounddevice as sd
import numpy as np
import time
import requests
import os

CANDIDATE_RATES = [48000, 44100]  # ← この順で試す
BLOCK = 1024
DB_THRESH = -25
BAND = (800, 2000)

# SwitchBot API設定
SWITCHBOT_TOKEN = os.getenv('SWITCHBOT_TOKEN', 'YOUR_TOKEN_HERE')
SWITCHBOT_DEVICE_ID_1 = os.getenv('SWITCHBOT_DEVICE_ID_1', 'YOUR_DEVICE_ID_HERE')
SWITCHBOT_DEVICE_ID_2 = os.getenv('SWITCHBOT_DEVICE_ID_2', 'YOUR_DEVICE_ID_HERE')
SWITCHBOT_API_BASE = 'https://api.switch-bot.com/v1.0'

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

def call_switchbot_api(device_id, command, parameter="default", command_type="command"):
    """
    SwitchBot APIを呼び出してデバイスを制御する

    Args:
        device_id: デバイスID
        command: コマンド名 (turnOn, turnOff, press など)
        parameter: コマンドパラメータ (デフォルト: "default")
        command_type: コマンドタイプ (デフォルト: "command")

    Returns:
        bool: 成功した場合True、失敗した場合False
    """
    url = f"{SWITCHBOT_API_BASE}/devices/{device_id}/commands"
    headers = {
        "Authorization": SWITCHBOT_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "command": command,
        "parameter": parameter,
        "commandType": command_type
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()

        if result.get('statusCode') == 100:
            print(f"✅ SwitchBot API成功: {command}")
            return True
        else:
            print(f"⚠️ SwitchBot API警告: {result.get('message', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ SwitchBot API エラー: {e}")
        return False

def on_chime_detected():
    print("🔔 音を感知しました！！")
    # SwitchBotのスイッチをONにする
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