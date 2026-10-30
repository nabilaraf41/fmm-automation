"""Synthesized sound effects (generated here, so FMM owns them: no licence risk).

python -m fmm.sfx   -> writes assets/sfx/*.wav
Sounds: whoosh, impact, riser, pop, click, type, ding, sparkle, stamp, flip
"""
import wave
from pathlib import Path
import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent.parent / "assets" / "sfx"
rng = np.random.default_rng(7)


def t(d): return np.linspace(0, d, int(SR * d), endpoint=False)
def env(n, a=0.005, r=0.2, curve=4.0):
    e = np.ones(n); na = max(1, int(SR * a)); e[:na] = np.linspace(0, 1, na)
    nr = min(n, int(SR * r)); e[-nr:] *= np.linspace(1, 0, nr) ** curve * 0 + (1 - np.linspace(0, 1, nr)) ** curve
    return e
def lowpass(x, k):  # simple one-pole, k in (0,1]: smaller = darker
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x): acc += k * (v - acc); y[i] = acc
    return y
def bandsweep(noise, k0, k1):
    ks = np.linspace(k0, k1, len(noise)); y = np.empty_like(noise); a = b = 0.0
    for i, v in enumerate(noise):
        a += ks[i] * (v - a); b += ks[i] * (a - b); y[i] = a - b * 0.6
    return y
def norm(x, peak=0.9): return x / (np.abs(x).max() + 1e-9) * peak


def whoosh(d=0.45):
    n = rng.standard_normal(int(SR * d))
    x = bandsweep(n, 0.02, 0.35)
    e = np.sin(np.linspace(0, np.pi, len(x))) ** 2
    return norm(x * e, 0.8)


def impact(d=0.9):
    tt = t(d)
    f = 120 * np.exp(-tt * 9) + 42
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5)
    crack = lowpass(rng.standard_normal(len(tt)), 0.4) * np.exp(-tt * 35)
    return norm(np.tanh(2.2 * (body + 0.5 * crack)), 0.95)


def riser(d=1.4):
    tt = t(d)
    f = 180 * (1 + 6 * (tt / d) ** 2)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    noise = bandsweep(rng.standard_normal(len(tt)), 0.01, 0.5)
    x = (tone + noise) * (tt / d) ** 1.6
    return norm(x, 0.7)


def pop(d=0.18):
    tt = t(d)
    f = 900 * np.exp(-tt * 30) + 300
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 28), 0.7)


def click(d=0.05):
    tt = t(d)
    return norm(rng.standard_normal(len(tt)) * np.exp(-tt * 180) + np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 120), 0.6)


def type_tick(d=0.04):
    tt = t(d)
    return norm(lowpass(rng.standard_normal(len(tt)), 0.6) * np.exp(-tt * 220), 0.45)


def ding(d=1.0):
    tt = t(d)
    x = sum(a * np.sin(2 * np.pi * f * tt) for f, a in ((1318.5, 1), (2637, .35), (3951, .15)))
    return norm(x * np.exp(-tt * 4.5), 0.6)


def sparkle(d=1.2):
    x = np.zeros(int(SR * d))
    for k in range(14):
        s = int(rng.uniform(0, d - 0.15) * SR); f = rng.uniform(2500, 6000); tt = t(0.15)
        x[s:s + len(tt)] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 40) * rng.uniform(.3, 1)
    return norm(x, 0.45)


def stamp(d=0.6):
    return norm(0.8 * impact(d) + 0.4 * np.concatenate([click(0.05), np.zeros(int(SR * d) - int(SR * 0.05))]), 0.95)


def flip(d=0.12):
    tt = t(d)
    return norm(bandsweep(rng.standard_normal(len(tt)), 0.3, 0.05) * np.exp(-tt * 30), 0.55)


SOUNDS = {"whoosh": whoosh, "impact": impact, "riser": riser, "pop": pop, "click": click, "type": type_tick,
          "ding": ding, "sparkle": sparkle, "stamp": stamp, "flip": flip}


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def load(name):
    p = OUT / f"{name}.wav"
    if not p.exists():
        build()
    with wave.open(str(p)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32767


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SOUNDS.items():
        write(OUT / f"{name}.wav", fn())


if __name__ == "__main__":
    build()
    print("wrote", sorted(p.name for p in OUT.glob("*.wav")))
