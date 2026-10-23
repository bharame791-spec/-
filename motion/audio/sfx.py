"""Synthesised sound design for the one-shot film, mixed under the voice-over.

Every cue is written in master-timeline seconds (the same clock film.js animates on)
and mapped to the 30s cut with the same RETIME curve, so sound and picture stay locked.

    python3 audio/sfx.py            -> audio/sfx.wav (stereo stem) + audio/mix.wav
"""
import os
import subprocess
import numpy as np

SR = 44100
DUR = 30.0
HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(7)

# keep in sync with RETIME in src/film.js  ([cut time, master time])
RETIME = [
    [0, 0], [2.2, 4.7], [3.3, 6.3], [4.35, 7.7], [5.4, 9.3], [6.95, 11.75],
    [9.6, 18.2], [10.95, 20.6], [12.9, 25.9], [14.15, 28.0], [15.0, 31.0],
    [17.0, 36.9], [21.4, 42.2], [22.8, 44.0], [23.6, 45.3], [24.3, 46.4],
    [25.3, 47.4], [27.2, 48.7], [28.8, 50.6], [30, 53],
]


def monotone(pts):
    x = np.array([p[0] for p in pts], float)
    y = np.array([p[1] for p in pts], float)
    d = np.diff(y) / np.diff(x)
    m = np.empty(len(x))
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(x) - 1):
        m[i] = 0 if d[i - 1] * d[i] <= 0 else 2 * d[i - 1] * d[i] / (d[i - 1] + d[i])

    def f(t):
        t = np.clip(t, x[0], x[-1])
        i = np.clip(np.searchsorted(x, t) - 1, 0, len(x) - 2)
        h = x[i + 1] - x[i]
        u = (t - x[i]) / h
        return ((2 * u**3 - 3 * u**2 + 1) * y[i] + (u**3 - 2 * u**2 + u) * h * m[i]
                + (-2 * u**3 + 3 * u**2) * y[i + 1] + (u**3 - u**2) * h * m[i + 1])
    return f


_fwd = monotone(RETIME)
_grid = np.linspace(0, DUR, 30001)
_mast = _fwd(_grid)


def cut(master_t):
    """master timeline seconds -> seconds in the 30s cut"""
    return float(np.interp(master_t, _mast, _grid))


# ------------------------------------------------------------------ synthesis
def env(n, a, r, curve=4.0):
    t = np.arange(n) / SR
    att = np.clip(t / max(a, 1e-4), 0, 1)
    rel = np.exp(-curve * np.clip(t - a, 0, None) / max(r, 1e-4))
    return att * rel


def svf_bandpass(x, f, q):
    """state-variable band-pass with a per-sample cutoff array"""
    f = np.broadcast_to(f, x.shape)
    low = band = 0.0
    out = np.empty_like(x)
    damp = 1.0 / q
    for i in range(len(x)):
        g = 2 * np.sin(np.pi * min(f[i], SR / 6) / SR)
        high = x[i] - low - damp * band
        band += g * high
        low += g * band
        out[i] = band
    return out


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a) * x[i] + a * acc
        y[i] = acc
    return y


def whoosh(dur, f0, f1, q=1.4, peak=0.55):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    sweep = f0 * (f1 / f0) ** t
    body = svf_bandpass(rng.standard_normal(n), sweep, q)
    shape = np.sin(np.pi * np.clip(t / peak, 0, 1) * 0.5) ** 2 * np.where(t > peak, np.cos(np.pi * 0.5 * (t - peak) / (1 - peak)) ** 2, 1)
    return body * shape * 0.5


def pop(freq=520, dur=0.16, drop=0.45, click=0.25):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 - drop * (1 - np.exp(-t * 40)))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, dur, 6)
    c = rng.standard_normal(n) * env(n, 0.0005, 0.006, 8) * click
    return s * 0.6 + svf_bandpass(c, np.full(n, 4000.0), 2)


def tick(freq=2600, dur=0.05):
    n = int(dur * SR)
    return svf_bandpass(rng.standard_normal(n), np.full(n, float(freq)), 6) * env(n, 0.0008, dur, 9) * 0.9


def knock(freq=180, dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = freq * (1 + 0.8 * np.exp(-t * 60))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, dur, 7) * 0.8
    c = tick(1400, 0.03)[:n]
    s[: len(c)] += c * 0.3
    return s


def chime(root=659.25, dur=2.4, partials=(1, 2.0, 3.0, 4.2), gain=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k, mul in enumerate(partials):
        s += np.sin(2 * np.pi * root * mul * t + k) * np.exp(-t * (2.2 + k * 1.6)) / (1 + k * 0.9)
    return s * env(n, 0.004, dur, 0.1) * gain


def boom(dur=2.2, f0=70, f1=38, gain=0.9):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 3)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.012, dur, 3.2)
    air = lowpass(rng.standard_normal(n), 420) * env(n, 0.005, 0.5, 5) * 2.2
    return (sub + air) * gain


def shimmer(dur=1.6, f=6500, gain=0.18):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    s = svf_bandpass(rng.standard_normal(n), np.full(n, float(f)), 3)
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t * dur)
    return s * np.sin(np.pi * t) ** 1.5 * trem * gain


def fwoom(dur=1.4):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    s = lowpass(rng.standard_normal(n), 900) * 3
    return s * (np.sin(np.pi * np.clip(t / 0.35, 0, 1) * 0.5) ** 2) * np.exp(-3 * np.clip(t - 0.35, 0, None)) * 0.5


def pad_swell(dur=4.0, root=110.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * root * m * t + m) / (1 + i) for i, m in enumerate((1, 1.5, 2, 3)))
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return lowpass(s, 1200) * shape * 0.14


# ------------------------------------------------------------------ cue sheet (master seconds)
out = np.zeros((int(DUR * SR) + SR * 3, 2))


def place(master_t, sig, gain=1.0, pan=0.0, at_cut=None):
    t = at_cut if at_cut is not None else cut(master_t)
    i = int(t * SR)
    sig = np.asarray(sig, float) * gain
    end = min(len(out), i + len(sig))
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    out[i:end, 0] += sig[: end - i] * l * 1.41
    out[i:end, 1] += sig[: end - i] * r * 1.41


# continuous bed: one unbroken room tone under the whole shot, so sound never "cuts" either
bed_n = int(DUR * SR)
bt = np.arange(bed_n) / SR
bed = lowpass(rng.standard_normal(bed_n), 700) * 0.5 * (0.7 + 0.3 * np.sin(2 * np.pi * bt / 11))
drone = sum(np.sin(2 * np.pi * f * bt + k) / (k + 1) for k, f in enumerate((98.0, 147.0, 196.0)))
drone = lowpass(drone, 600) * (0.6 + 0.4 * np.sin(2 * np.pi * bt / 7.5 - 1.5) ** 2)
bed = (bed * 0.5 + drone * 0.05) * np.clip(bt / 1.2, 0, 1)
place(0, bed, 0.9, at_cut=0)

# scene 1 — beans gather, hero bean becomes the dalla
place(0, pad_swell(3.6, 98.0), 1.0)
for i in range(6):
    a = i * np.pi / 3
    place(0.45 + 0.2 * i, whoosh(0.6, 700, 2400, peak=0.6), 0.32, pan=float(np.cos(a)) * 0.7)
place(2.8, whoosh(0.7, 300, 1800, q=1.0, peak=0.85), 0.5)
place(3.8, shimmer(1.2, 7000), 1.0)
place(4.7, tick(2200), 0.55)
place(4.85, tick(2600), 0.45)
place(4.9, pop(980, 0.12), 0.3)
# scene 2 — ingredients, flame, dalla completes
place(5.1, whoosh(1.1, 400, 1300, peak=0.5), 0.3)
place(6.7, whoosh(0.8, 900, 400, peak=0.4), 0.35)
for j in range(6):
    place(7.9 + 0.08 * j, knock(240 + j * 18, 0.12), 0.35, pan=float(np.cos(j * np.pi / 3)) * 0.4)
place(7.5, pop(760, 0.14), 0.4)
place(8.7, whoosh(0.8, 600, 2400, peak=0.35), 0.4, pan=0.7)
place(8.9, whoosh(0.8, 2200, 700, peak=0.5), 0.35, pan=-0.7)
place(9.9, pop(380, 0.2, drop=0.6, click=0.6), 0.55)
for s in range(7):
    place(10.1 + s * 0.05, tick(3200 + s * 180, 0.035), 0.22, pan=float(np.sin(s)) * 0.5)
for s in range(7):
    place(10.8 + s * 0.03, tick(2400, 0.03), 0.18)
place(11.5, whoosh(1.0, 500, 1600, peak=0.7), 0.3)
place(12.7, fwoom(1.4), 0.9)
place(12.6, shimmer(1.6, 6000), 0.9)
# pour → grid
place(15.0, whoosh(2.6, 1800, 220, q=1.1, peak=0.45), 0.6)
for k in range(7):
    place(17.0 + k * 0.08, tick(1900 + k * 120, 0.04), 0.25, pan=(3 - k) / 4)
for k in range(8):
    place(17.3 + k * 0.07, tick(2800 - k * 90, 0.035), 0.2)
place(17.9, tick(3000), 0.4)
place(18.2, knock(150, 0.3), 0.7)
place(18.9, whoosh(0.5, 2500, 900, peak=0.3), 0.3)
for k, f in enumerate((620, 740, 880)):
    place(19.2 + k * 0.15, pop(f, 0.13), 0.35, pan=-0.4)
place(20.3, whoosh(0.5, 900, 2600, peak=0.4), 0.25)
place(20.6, knock(170, 0.3), 0.6)
place(21.1, pop(990, 0.12), 0.3, pan=-0.4)
place(21.3, pop(640, 0.18, click=0.4), 0.5)
place(21.3, chime(659.25, 2.2), 0.8)
# applications
place(23.6, whoosh(1.4, 300, 1500, q=1.2, peak=0.8), 0.55)
place(25.0, knock(120, 0.35), 0.6)
place(25.9, tick(2400), 0.4)
place(26.04, tick(2100), 0.35)
place(26.0, pop(300, 0.16, drop=0.3, click=0.8), 0.4)
place(26.3, whoosh(0.7, 2000, 800, peak=0.3), 0.3, pan=0.6)
place(26.45, whoosh(0.7, 1800, 700, peak=0.3), 0.3, pan=-0.2)
place(26.6, whoosh(0.7, 1600, 600, peak=0.3), 0.3, pan=-0.6)
place(28.0, tick(2600), 0.4)
place(28.8, shimmer(0.9, 5500), 0.8)
for k in range(3):
    place(29.2 + k * 0.12, pop(880 + k * 110, 0.1), 0.3)
place(31.0, whoosh(1.6, 2400, 300, q=1.0, peak=0.25), 0.45)
place(33.6, shimmer(1.8, 6500), 0.8)
# designer reveal
place(36.5, boom(2.4), 0.8)
place(36.5, shimmer(1.4, 8000), 0.7)
place(36.9, whoosh(0.9, 700, 2200, peak=0.6), 0.3)
place(38.2, whoosh(0.6, 1200, 3000, peak=0.7), 0.25)
place(38.6, pop(700, 0.18, click=0.4), 0.5)
place(38.6, chime(523.25, 2.4), 0.6)
place(38.8, tick(2800), 0.3)
place(42.2, whoosh(0.9, 800, 2000, peak=0.6), 0.3)
for k in range(4):
    place(42.7 + k * 0.1, pop(1040 + k * 60, 0.1), 0.25, pan=(-0.6, 0.6, -0.6, 0.6)[k])
# CTA
place(44.0, whoosh(1.1, 2200, 500, peak=0.4), 0.45)
place(44.9, shimmer(1.3, 6000), 0.8)
place(45.3, boom(1.6, 90, 50, 0.6), 0.75)
place(45.3, knock(200, 0.25), 0.5)
place(45.9, whoosh(0.7, 900, 2600, peak=0.6), 0.25, pan=0.4)
place(46.7, pop(880, 0.1, click=0.2), 0.45, pan=0.5)
place(46.8, pop(1320, 0.12, click=0.1), 0.4, pan=0.5)
place(46.4, whoosh(1.2, 500, 1400, peak=0.75), 0.35, pan=-0.6)
for k in range(3):
    place(46.4 + k * 0.16, tick(2500 - k * 150), 0.3)
place(47.4, tick(2700), 0.3)
place(48.7, shimmer(0.9, 6000), 0.7)
place(48.7, chime(659.25, 3.0, gain=0.4), 0.9)
place(48.75, chime(987.77, 3.0, gain=0.25), 0.7)

# ------------------------------------------------------------------ space + master
ir_n = int(1.6 * SR)
tt = np.arange(ir_n) / SR
ir = np.stack([rng.standard_normal(ir_n), rng.standard_normal(ir_n)], 1) * np.exp(-tt * 4.2)[:, None]
ir[:, 0] = lowpass(ir[:, 0], 5000)
ir[:, 1] = lowpass(ir[:, 1], 5000)
ir /= np.sqrt((ir**2).sum(0))
L = len(out) + ir_n
wet = np.stack([np.fft.irfft(np.fft.rfft(out[:, c], L) * np.fft.rfft(ir[:, c], L), L)[: len(out)] for c in range(2)], 1)
sfx = out * 0.8 + wet * 0.45
sfx = sfx[: int(DUR * SR)]


def read(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(float)


def write(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(SR), '-ac', str(x.shape[1]), '-i', '-', path],
                   input=pcm, check=True)


vo = read(os.path.join(HERE, 'vo-cut.wav'))
vo = np.pad(vo, (0, max(0, len(sfx) - len(vo))))[: len(sfx)]
# duck the sound design under the voice so every word stays in front
lvl = np.sqrt(np.convolve(vo**2, np.ones(2205) / 2205, mode='same'))
duck = 1 - 0.45 * np.clip(lvl / 0.05, 0, 1)
duck = np.convolve(duck, np.ones(4410) / 4410, mode='same')
sfx *= duck[:, None]
sfx /= max(1e-9, np.abs(sfx).max()) / 0.5

write(os.path.join(HERE, 'sfx.wav'), sfx)
mix = sfx * 0.55 + np.stack([vo, vo], 1) * (0.9 / max(1e-9, np.abs(vo).max()))
fade = int(0.8 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
write(os.path.join(HERE, 'mix-raw.wav'), mix)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(HERE, 'mix-raw.wav'),
                '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', str(SR), os.path.join(HERE, 'mix.wav')], check=True)
os.remove(os.path.join(HERE, 'mix-raw.wav'))
print('cues mapped e.g. name reveal master 36.9 ->', round(cut(36.9), 2), 's')
