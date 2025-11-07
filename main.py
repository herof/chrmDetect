import sounddevice as sd
import numpy as np
import time

CANDIDATE_RATES = [48000, 44100]  # ← この順で試す
BLOCK = 1024
DB_THRESH = -25
BAND = (800, 2000)

sd.default.device = ("USB デバイスが見つからないです", None)

def pick_working_rate():
    for r in CANDIDATE_RATES:
        try:
            with sd.InputStream(channels=1, samplerate=r, blocksize=BLOCK, dtype='float32'):
                return r
        except Exception as e:
            # print(f"rate {r} failed: {e}")
            pass
    raise RuntimeError("No supported sample rate found")

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

def on_chime_detected():
    print("🔔 音を感知しました！!")

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