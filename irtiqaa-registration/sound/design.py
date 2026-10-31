"""Sound design + mix for the Irtiqaa registration video.

All SFX are synthesised here (modal metal, Karplus-Strong plucks, granular sand/paper,
spectrally-shaped noise whooshes, convolution reverb) and placed on the exact animation
timestamps from index.html. Output: mix.wav (VO + SFX + ambient bed, loudness-ready).
Usage: python3 design.py <vo.mp3> <out_dir>
"""
import sys, subprocess, numpy as np, soundfile as sf
from scipy import signal

SR = 48000
DUR = 67.0
N = int(DUR * SR)
rng = np.random.default_rng(11)
VO_OFFSET = 3.0
TS = [21.2, 25.9, 30.75, 36.0, 40.85]          # station starts (index.html)
FT = [9.8, 11.8, 14.6, 17.3, 18.5, 18.8]        # ticket fields

# ------------------------------------------------------------------ buses
B = {k: np.zeros((N, 2)) for k in ('dry', 'send', 'bed')}
def place(x, t, g=1.0, pan=0.0, send=0.25, bus='dry'):
    if x.ndim == 1: x = pan2(x, pan)
    i = int(round(t * SR))
    if i < 0: x, i = x[-i:], 0
    j = min(N, i + len(x))
    if j <= i: return
    B[bus][i:j] += x[:j - i] * g
    if bus == 'dry' and send: B['send'][i:j] += x[:j - i] * g * send

# ------------------------------------------------------------------ helpers
def tt(d): return np.arange(int(d * SR)) / SR
def pan2(x, p):
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], 1)
def norm(x, peak=1.0):
    m = np.max(np.abs(x)); return x * (peak / m) if m > 0 else x
def flt(x, kind, f, o=2):
    sos = signal.butter(o, f, kind, fs=SR, output='sos'); return signal.sosfilt(sos, x, axis=0)
def env_ar(n, a, r, curve=3.0):
    t = np.arange(n) / SR
    e = np.where(t < a, (t / max(a, 1e-4)) ** 2, np.exp(-(t - a) * curve / max(r, 1e-4)))
    return e
def noise(d): return rng.standard_normal(int(d * SR))

def shaped(d, fc, bw, nper=1024):
    """noise with a time-varying log-gaussian band: fc(u)->Hz, bw(u)->octaves, u in 0..1"""
    n = int(d * SR); x = rng.standard_normal(n + nper)
    f, t, Z = signal.stft(x, SR, nperseg=nper, noverlap=nper * 3 // 4)
    u = np.clip(t / d, 0, 1)
    lf = np.log2(np.maximum(f, 15))[:, None]
    FC = np.log2(np.vectorize(fc)(u))[None, :]
    BW = np.vectorize(bw)(u)[None, :]
    Z *= np.exp(-0.5 * ((lf - FC) / BW) ** 2)
    _, y = signal.istft(Z, SR, nperseg=nper, noverlap=nper * 3 // 4)
    return norm(y[:n])

def smooth_env(n, pts):
    """piecewise-smooth envelope from [(u,val),...]"""
    u = np.linspace(0, 1, n); xs, ys = zip(*pts)
    e = np.interp(u, xs, ys); k = max(1, n // 200)
    return np.convolve(e, np.ones(k) / k, 'same')

# ------------------------------------------------------------------ reverb
def make_ir(rt=2.6, dur=3.2, pre=0.018):
    n = int(dur * SR); t = np.arange(n) / SR; ir = np.zeros((n, 2))
    for c in range(2):
        x = rng.standard_normal(n) * np.exp(-t * 6.9 / rt)
        dark = flt(x, 'low', 2200); w = np.clip(t / (dur * .6), 0, 1)
        ir[:, c] = x * (1 - w) + dark * w * 1.4
    ir[:int(pre * SR)] = 0
    # early reflections
    for d, g in [(.011, .5), (.019, .4), (.027, .32), (.041, .25)]:
        ir[int((pre + d) * SR), 0] += g; ir[int((pre + d * 1.13) * SR), 1] += g
    return ir / np.sqrt((ir ** 2).sum() / 2)
def convolve_st(x, ir):
    return np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:len(x)] for c in range(2)], 1)

# ------------------------------------------------------------------ instruments
def whoosh(d, f0=300, f1=2500, f2=700, peak=.62, bw=1.1, pan=(-.5, .5), air=.35):
    core = shaped(d, lambda u: f0 * (f1 / f0) ** min(u / peak, 1) if u < peak else f1 * (f2 / f1) ** ((u - peak) / (1 - peak)),
                  lambda u: bw)
    hiss = shaped(d, lambda u: 6000 + 3000 * u, lambda u: .9)
    n = len(core); u = np.linspace(0, 1, n)
    e = np.where(u < peak, (u / peak) ** 2.2, np.exp(-((u - peak) / (1 - peak)) * 4.5))
    y = (core + hiss * air) * e
    p = np.linspace(pan[0], pan[1], n); a = (p + 1) * np.pi / 4
    return norm(np.stack([y * np.cos(a), y * np.sin(a)], 1), .9)

def sub_hit(d=3.0, f0=70, f1=32, decay=2.0, click=.5, body=.6):
    t = tt(d); f = f1 + (f0 - f1) * np.exp(-t * 4)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * decay)
    s = np.tanh(s * 1.6)
    b = flt(noise(d), 'low', 380) * np.exp(-t * 14) * body
    c = flt(noise(d), 'high', 2500) * np.exp(-t * 180) * click
    return norm(s + b + c)

def reverse_swell(d=1.6, fc=(800, 6000)):
    y = shaped(d, lambda u: fc[0] * (fc[1] / fc[0]) ** u, lambda u: 1.4)
    e = np.linspace(0, 1, len(y)) ** 3.2
    return norm(y * e)

def bell(f, d=2.2, ratios=(1, 2.0, 3.01, 4.17, 5.43), dec=(1.0, 1.8, 2.6, 3.8, 5.0), amps=(1, .5, .32, .2, .12)):
    t = tt(d); y = np.zeros_like(t)
    for r, k, a in zip(ratios, dec, amps):
        y += a * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6)) * np.exp(-t * k * 2.2)
    y *= np.minimum(1, t / .003)
    return norm(y)

HIJAZ = [293.66, 311.13, 369.99, 392.0, 440.0, 466.16, 523.25]   # D Eb F# G A Bb C
def hz(deg, octv=0):
    o, i = divmod(deg, 7); return HIJAZ[i] * 2 ** (o + octv)

def shimmer(d, dens=26, octv=2, gain_curve=None, spread=.8):
    n = int(d * SR); y = np.zeros((n + int(2.5 * SR), 2))
    cnt = int(dens * d)
    for _ in range(cnt):
        u = rng.uniform(0, 1)
        if gain_curve is not None and rng.uniform() > gain_curve(u): continue
        g = bell(hz(rng.integers(0, 10), octv), 1.6) * rng.uniform(.25, .7)
        i = int(u * n); y[i:i + len(g)] += pan2(g, rng.uniform(-spread, spread))
    return y

def ks_pluck(f, d=2.0, bright=.5, damp=.996):
    n = int(d * SR); p = int(SR / f)
    buf = rng.uniform(-1, 1, p); buf = flt(buf, 'low', 1500 + 7000 * bright)
    out = np.zeros(n); idx = 0; prev = 0.0
    for i in range(n):
        v = buf[idx]; nv = damp * .5 * (v + prev); prev = v
        buf[idx] = nv; out[i] = v; idx += 1
        if idx >= p: idx = 0
    out *= np.minimum(1, np.arange(n) / 60)
    return norm(out)

def click(d=.03, f=2200, q_dec=140, body_f=320, body=.5, tick=.6):
    t = tt(d)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * q_dec)
    y += body * np.sin(2 * np.pi * body_f * t) * np.exp(-t * 90)
    y += tick * flt(noise(d), 'high', 3500) * np.exp(-t * 900)
    return norm(y)

def flap_flurry(n=7, span=.24, final=1.0):
    d = span + .1; y = np.zeros(int(d * SR))
    ts = np.sort(rng.uniform(0, span, n)); ts[-1] = span
    for k, t0 in enumerate(ts):
        c = click(.03, rng.uniform(1900, 2900), 160, rng.uniform(260, 360), .6, .7) * (rng.uniform(.4, .7) if k < n - 1 else final)
        i = int(t0 * SR); y[i:i + len(c)] += c[:len(y) - i]
    return norm(y)

def modal(freqs, decs, amps, d, strike=.002):
    t = tt(d); y = np.zeros_like(t)
    for f, k, a in zip(freqs, decs, amps):
        y += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / k)
    y *= np.minimum(1, t / strike)
    return norm(y)

def creak(d, f0=55, f1=38, res=(700, 1300)):
    """stick-slip friction: jittered pulse train through resonant band"""
    n = int(d * SR); y = np.zeros(n); t = 0.0
    while t < d:
        u = t / d; f = f0 + (f1 - f0) * u
        i = int(t * SR)
        if i < n: y[i] = rng.uniform(.5, 1)
        t += (1 / f) * rng.uniform(.75, 1.3)
    y = flt(y, 'band', list(res), 2) + .4 * flt(y, 'band', [140, 260], 2)
    e = smooth_env(n, [(0, 0), (.1, 1), (.6, .8), (.85, .9), (1, 0)])
    return norm(y * e)

def grain_cloud(d, rate, band=(1500, 7000), gl=.0008):
    n = int(d * SR); y = np.zeros(n); k = int(rate * d)
    g = np.hanning(int(gl * SR)) * 1.0
    for _ in range(k):
        i = rng.integers(0, max(1, n - len(g))); y[i:i + len(g)] += g * rng.standard_normal(len(g)) * rng.uniform(.3, 1)
    return norm(flt(y, 'band', list(band), 2))

def paper(d=.25, f=(1400, 5200), rate=1800):
    y = grain_cloud(d, rate, f, .0012) + .6 * shaped(d, lambda u: 2600 - 900 * u, lambda u: 1.0)
    return norm(y * env_ar(len(y), d * .2, d * .8, 4))

def footstep_sand(intensity=1.0):
    d = .28; n = int(d * SR); t = tt(d)
    crunch = grain_cloud(d, 2600, (1200, 8000), .0006) * np.exp(-((t - .05) / .045) ** 2)
    thump = flt(noise(d), 'low', 220) * np.exp(-t * 30)
    return norm((crunch * .9 + thump * .5)) * intensity

def drop_plop():
    d = .7; t = tt(d)
    f = 650 + 1800 * (1 - np.exp(-t * 60))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38)
    splash = flt(noise(d), 'high', 3000) * np.exp(-t * 55) * .35
    bub = np.sin(2 * np.pi * np.cumsum(420 + 300 * np.exp(-t * 25)) / SR) * np.exp(-((t - .08) / .02) ** 2) * .4
    return norm(tone + splash + bub)

# ------------------------------------------------------------------ SCORE
def sizzle(t0, t1, g=.10):
    d = t1 - t0
    y = shaped(d, lambda u: 7000 + 2000 * np.sin(u * 9), lambda u: .6)
    y *= smooth_env(len(y), [(0, 0), (.15, 1), (.85, .9), (1, 0)])
    place(pan2(y, 0), t0, g, send=.5)
    place(shimmer(d, 10, 2), t0, g * .9, send=.9)

# --- S1 gate (0–5)
place(shaped(6.0, lambda u: 70, lambda u: 1.2) * smooth_env(int(6 * SR), [(0, 0), (.25, 1), (.7, .8), (1, 0)]), 0.0, .28, send=.2)   # dark hall rumble
rs = reverse_swell(0.85, (500, 5000)); place(rs, 0.75, .30, send=.6)
place(shimmer(0.8, 18, 2), 0.85, .22, send=1.0)
place(click(.08, 1450, 45, 180, 1.0, .9), 1.55, .55, send=.4)                          # latch
gate = modal([58, 87, 131, 197, 263, 347, 452, 618, 811], [3.0, 2.6, 2.2, 1.7, 1.4, 1.1, .8, .5, .35],
             [1, .8, .6, .55, .45, .35, .3, .22, .15], 4.5)
place(gate, 1.6, .55, send=.55)
place(sub_hit(3.5, 64, 30, 1.6, .2, .8), 1.6, .65, send=.35)
place(creak(1.5, 48, 34), 1.7, .22, pan=-.35, send=.3)
place(creak(1.5, 52, 36, (800, 1500)), 1.72, .20, pan=.35, send=.3)
place(whoosh(1.6, 180, 900, 300, .55, 1.0, (-.7, .7), .2), 1.6, .38, send=.3)
place(shimmer(1.8, 22, 1), 2.0, .25, send=1.0)                                            # light pouring
sizzle(2.3, 5.0, .07)
place(whoosh(1.5, 250, 3000, 900, .6, 1.0, (.3, -.2)), 3.45, .45)                         # camera up

# --- S2 board (4.5–6.2)
place(sub_hit(.6, 140, 80, 9, .4, .6), 4.55, .30, send=.15)                               # board settles
for t0 in [5.0, 5.15, 5.3, 5.52, 5.72, 5.92]:
    place(flap_flurry(rng.integers(6, 10), .2), t0, .42, pan=rng.uniform(-.25, .25), send=.12)
place(bell(880, 2.0) * .7 + bell(1174.66, 2.0) * .5, 6.15, .22, send=.5)                 # status chime
place(click(.04, 3200, 220, 400, .3, .5), 6.15, .25, pan=.5, send=.1)                    # lamp

# --- S3 ticket (6.6–21.7)
place(whoosh(1.7, 900, 2200, 300, .45, 1.0, (.2, -.3)), 6.5, .38)                          # camera down
dprint = 2.0; tp = tt(dprint)
motor = (signal.sawtooth(2 * np.pi * 96 * tp) * .4 + np.sin(2 * np.pi * 192 * tp) * .3) * (.6 + .4 * (signal.square(2 * np.pi * 22 * tp) > 0))
motor = flt(motor, 'low', 900) * smooth_env(len(tp), [(0, 0), (.06, 1), (.9, 1), (1, 0)])
place(norm(motor), 6.9, .16, send=.1)
place(paper(2.0, (1200, 6000), 900) * smooth_env(int(2 * SR), [(0, 0), (.1, 1), (.9, .8), (1, 0)]), 6.9, .30, send=.15)
place(click(.05, 1800, 120, 240, .8, .6), 8.88, .35, send=.15)                             # ticket stops
for f in FT: place(paper(.12, (2500, 7000), 2500), f + .05, .14, pan=rng.uniform(-.3, .3), send=.1)
sizzle(19.2, 20.1, .10)
place(whoosh(.9, 800, 5000, 2000, .7, .8, (.8, 0)), 19.25, .30)
punch = modal([2480, 3710, 5120, 6890], [.03, .022, .015, .01], [1, .7, .5, .3], .12)
place(punch, 20.1, .55, send=.2); place(sub_hit(.5, 160, 90, 14, .6, .5), 20.1, .45, send=.2)
place(paper(.18, (2000, 7000), 4000), 20.13, .3, send=.2)
for k in range(6): place(paper(.06, (3000, 9000), 4000), 20.18 + k * .07, .08, pan=rng.uniform(-.7, .7), send=.3)
# zoom through the hole → light
riser = shaped(2.3, lambda u: 300 * (8000 / 300) ** (u ** 1.4), lambda u: 1.1) * np.linspace(0, 1, int(2.3 * SR)) ** 2.6
place(pan2(norm(riser), 0), 19.45, .40, send=.5)
place(shimmer(2.0, 30, 2, lambda u: u ** 1.5), 19.7, .30, send=1.0)
place(reverse_swell(1.3, (1200, 9000)), 20.45, .35, send=.5)
place(sub_hit(4.0, 52, 28, 1.1, .1, .5), 21.72, .55, send=.6)
place(shimmer(2.5, 16, 2, lambda u: 1 - u), 21.72, .30, send=1.0)
place(bell(587.33, 3.5) * .6 + bell(880, 3.5) * .45 + bell(1174.66, 3.5) * .3, 21.75, .22, send=.8)

# --- S4 stations
for k in range(1, 5):                                                                     # climb whooshes
    place(whoosh(1.25, 220, 2600, 800, .55, 1.05, (.5, -.5)), TS[k] - .2, .40)
    place(sub_hit(.8, 90, 50, 6, .05, .4), TS[k] + .95, .18, send=.3)                   # land on step
T = TS[0]                                                                                 # Quran
sizzle(T + 1.0, T + 2.8, .07)
for k in range(3): place(paper(.22, (1100, 4800), 1500), T + 1.55 + k * .2, .32, pan=-.2 + .2 * k, send=.25)
place(shimmer(1.2, 22, 2), T + 2.4, .22, send=1.0)
place(sub_hit(.9, 120, 60, 7, .7, 1.0), T + 3.65, .62, send=.3)                          # stamp
place(click(.06, 900, 60, 140, 1.0, .9), T + 3.65, .40, send=.2)
place(paper(.15, (1500, 6000), 3000), T + 3.68, .18, send=.2)
T = TS[1]                                                                                 # Aqeedah
place(sub_hit(2.5, 75, 38, 1.8, .1, .3), T + 1.0, .32, send=.6)
place(bell(146.83, 4.0) * .5 + bell(293.66, 4.0) * .3, T + 1.0, .22, send=.8)
wd = 3.1; wind = shaped(wd, lambda u: 380 + 380 * np.sin(u * 7) ** 2 + 300 * u, lambda u: .75)
whistle = shaped(wd, lambda u: 1100 + 500 * np.sin(u * 11), lambda u: .12)
we = smooth_env(int(wd * SR), [(0, 0), (.18, .8), (.35, 1), (.55, .85), (.75, .35), (1, 0)])
wst = np.stack([(wind + whistle * .35) * we, (np.roll(wind, 2400) + np.roll(whistle, 1800) * .35) * we], 1)
place(norm(wst), T + 1.45, .42, send=.35)
for i in range(4): place(whoosh(.7, 400, 1800, 500, .5, .9, (-.8 + .5 * i, .8 - .5 * i), .1), T + 1.6 + i * .42, .14)
place(bell(587.33, 3.0) * .5 + bell(880, 3.0) * .5, T + 3.95, .25, send=.9)            # calm
place(shimmer(1.6, 18, 2, lambda u: 1 - u), T + 3.95, .2, send=1.0)
T = TS[2]                                                                                 # Seerah
place(pan2(norm(shaped(1.0, lambda u: 1500, lambda u: 1.4) * env_ar(int(SR), .35, .65)), 0), T + .65, .20, send=.2)
for j in range(5): place(paper(.14, (1500, 5500), 2200), T + 1.12 + .12 * j, .16, pan=-.4 + .2 * j, send=.2)
def io(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
for j in range(9):
    f = .06 + .1 * j; lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo + hi) / 2
        if io(m) < f + .02: lo = m
        else: hi = m
    place(footstep_sand(1 - .06 * j), T + 1.6 + 2.0 * lo, .40 * (1 - .05 * j), pan=(-.25 if j % 2 else .25), send=.2)
T = TS[3]                                                                                 # Ibadat
sizzle(T + .9, T + 1.7, .06)
place(drop_plop() * .4, T + 1.25, .15, send=.6)
place(whoosh(.4, 2000, 4000, 1500, .8, .7, (0, 0), .1), T + 1.85, .10)
place(drop_plop(), T + 2.25, .55, send=.75)
place(sub_hit(1.2, 90, 50, 4, 0, .2), T + 2.25, .15, send=.6)
for j, deg in enumerate([0, 2, 3, 4, 5, 7, 9, 11]):
    place(ks_pluck(hz(deg), 2.2, .55), T + 2.6 + j * .09, .17, pan=-.5 + j * .14, send=.6)
place(shimmer(1.5, 16, 2), T + 3.2, .17, send=1.0)
T = TS[4]                                                                                 # Akhlaq
place(sub_hit(.9, 100, 55, 5, .1, .9), T + .6, .25, send=.2)
place(pan2(norm(shaped(1.0, lambda u: 600 + 500 * u, lambda u: 1.0) * env_ar(int(SR), .2, .8)), 0), T + .62, .14, send=.2)
sizzle(T + .9, T + 1.5, .06)
place(creak(.6, 30, 24, (250, 600)), T + 1.4, .13, send=.3)
grow = shaped(1.1, lambda u: 200 * 15 ** u, lambda u: 1.0) * np.linspace(0, 1, int(1.1 * SR)) ** 1.5
place(pan2(norm(grow), 0), T + 1.75, .22, send=.5)
for i, deg in enumerate([7, 9, 10, 11, 12, 14]):
    place(ks_pluck(hz(deg), 2.0, .7), T + 2.68 + .18 * i, .26, pan=[-.5, .5, -.4, .4, -.2, .2][i], send=.55)
    place(paper(.08, (2000, 7000), 3000), T + 2.66 + .18 * i, .10, send=.2)

# --- S5 reveal (44.4–54)
place(whoosh(1.1, 300, 2500, 900, .55, 1.0, (.4, -.4)), 44.35, .32)
place(whoosh(1.4, 1500, 400, 120, .2, 1.2, (-.6, .6), .5), 44.95, .42)                    # pull back
place(reverse_swell(.75, (800, 9000)), 45.75, .45, send=.4)
place(sub_hit(4.5, 60, 28, .9, .6, 1.0), 46.45, .85, send=.7)                             # BIG hit — logo bar
place(bell(293.66, 5) * .5 + bell(440, 5) * .45 + bell(587.33, 5) * .4 + bell(1174.66, 5) * .2, 46.47, .30, send=.9)
place(shimmer(2.2, 28, 2, lambda u: 1 - u * .8), 46.5, .25, send=1.0)
sizzle(46.8, 48.1, .07)
for t0 in [48.4, 48.6]: place(whoosh(.6, 1500, 4000, 2000, .6, .8, (.6, -.6), .4), t0, .10)
for i, st in enumerate([49.1, 50.55, 51.75, 53.05]):
    wood = modal([690, 1810, 3120], [.05, .03, .015], [1, .5, .25], .2)
    place(wood, st + .33, .30, pan=(.35 if i % 2 == 0 else -.35), send=.3)
    place(ks_pluck(hz([4, 7, 9, 11][i]), 1.8, .45), st + .33, .14, pan=(.35 if i % 2 == 0 else -.35), send=.6)
place(whoosh(.9, 600, 3500, 1200, .6, 1.0, (0, 0)), 53.75, .30)

# --- S6 ticket flip / QR (54–60)
place(whoosh(1.0, 300, 2000, 600, .55, 1.0, (-.2, .2)), 53.95, .38)
place(paper(.3, (1200, 5000), 1500), 54.7, .25, send=.2)
place(whoosh(.85, 900, 4200, 1200, .55, .7, (.7, -.7), .5), 55.2, .40)
place(paper(.12, (2000, 7000), 3000), 55.95, .30, send=.2)
place(bell(1174.66, 3.0) * .6 + bell(1760, 3.0) * .4, 56.0, .30, send=.9)               # QR reveal
place(shimmer(1.4, 20, 2, lambda u: 1 - u), 56.0, .22, send=1.0)
place(whoosh(.8, 500, 3000, 1500, .6, 1.0, (0, 0)), 59.5, .35)

# --- S7 end card (59.7–67)
place(whoosh(.7, 300, 1500, 400, .7, 1.0, (0, 0)), 59.7, .28)
place(sub_hit(.8, 130, 70, 8, .5, .9), 60.28, .40, send=.2)
for t0 in [60.1, 60.45]: place(flap_flurry(9, .24), t0, .42, send=.12)
place(bell(880, 2.0) * .7 + bell(1174.66, 2.0) * .5, 60.75, .25, send=.5)
place(click(.04, 3200, 220, 400, .3, .5), 60.75, .25, pan=.5, send=.1)
place(shimmer(1.2, 18, 2, lambda u: 1 - u), 60.85, .2, send=1.0)
place(whoosh(.8, 400, 1600, 600, .6, 1.0, (0, 0), .2), 61.4, .18)
sizzle(63.2, 64.1, .10)
place(whoosh(.9, 800, 4500, 2000, .7, .8, (.9, .1)), 63.2, .22)
place(sub_hit(5.0, 58, 28, .8, .3, .8), 64.1, .65, send=.8)                               # final hit
place(bell(293.66, 5) * .5 + bell(587.33, 5) * .45 + bell(880, 5) * .35 + bell(1760, 5) * .15, 64.12, .30, send=.9)
place(shimmer(1.2, 40, 2), 64.0, .30, send=1.0)                                           # glint

# ------------------------------------------------------------------ ambient bed (D Hijaz)
def pad_note(f, d, cutoff):
    t = tt(d); y = np.zeros((len(t), 2))
    for c in range(2):
        for k, det in enumerate([-7, -2.5, 2.5, 7]):
            ff = f * 2 ** ((det + (c - .5) * 3) / 1200)
            y[:, c] += signal.sawtooth(2 * np.pi * ff * t + rng.uniform(0, 6)) * .25
    return flt(y, 'low', cutoff, 2)
def pad_chord(notes, t0, t1, cutoff, g, fade=2.0):
    d = t1 - t0 + fade
    y = sum(pad_note(f, d, cutoff) for f in notes) / len(notes) ** .5
    e = smooth_env(len(y), [(0, 0), (min(.45, fade / d), 1), (max(.55, 1 - fade / d), 1), (1, 0)])
    place(y * e[:, None], t0 - fade / 2, g, bus='bed')
D2, A2, D3, Fs3, A3, D4, G2, Bb2, G3, Bb3, C3, Eb3 = 73.42, 110.0, 146.83, 185.0, 220.0, 293.66, 98.0, 116.54, 196.0, 233.08, 130.81, 155.56
pad_chord([D2, A2], 0.0, 21.7, 420, .55, 3.0)                                             # dark hall drone
pad_chord([D2, A2, D3], 2.0, 21.7, 650, .30, 3.0)
pad_chord([D2, A2, D3, Fs3, A3], 21.6, 30.75, 1600, .55, 1.6)                            # light: D major (Hijaz root)
pad_chord([G2, D3, G3, Bb3], 30.75, 36.0, 1500, .55)                                      # Gm
pad_chord([C3, Eb3, G3, D3 * 2], 36.0, 40.85, 1500, .50)                                  # Cm(add9)
pad_chord([D2, A2, D3, Fs3, A3], 40.85, 46.4, 1700, .55)
pad_chord([D2, A2, D3, Fs3, A3, D4], 46.4, 53.9, 2200, .62, 1.0)                          # reveal, open
pad_chord([G2, D3, G3, Bb3], 53.9, 59.7, 1800, .55)
pad_chord([D2, A2, D3, Fs3, A3, D4], 59.7, 66.0, 2300, .62, 1.6)
# gentle pulse (plucked ostinato) through the stations, keeps the climb moving
pat = [0, 4, 7, 4, 5, 4, 2, 4]
t0 = 21.75; i = 0
while t0 < 46.3:
    deg = pat[i % 8] + (3 if 30.75 <= t0 < 36 else 0)
    place(ks_pluck(hz(deg, -1), 1.4, .25, .993), t0, .10, pan=(-.3 if i % 2 else .3), send=.5, bus='bed')
    t0 += .5; i += 1

# ------------------------------------------------------------------ mix
def main(vo_path, out):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', vo_path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    vo = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    V = np.zeros((N, 2)); i = int(VO_OFFSET * SR); V[i:i + len(vo)] = vo[:N - i]
    ir = make_ir()
    sfx = B['dry'] + convolve_st(B['send'], ir) * .55
    bed = B['bed'] * .55 + convolve_st(B['bed'], make_ir(3.5, 4.0)) * .5
    # VO-driven ducking
    lvl = np.sqrt(np.convolve(V.mean(1) ** 2, np.ones(2400) / 2400, 'same'))
    on = (lvl > .02).astype(float)
    k = int(.25 * SR); on = np.convolve(on, np.ones(k) / k, 'same')
    duck_bed = 1 - .45 * np.clip(on, 0, 1); duck_sfx = 1 - .30 * np.clip(on, 0, 1)
    vo_g = 10 ** (0 / 20)
    mix = V * vo_g + sfx * .55 * duck_sfx[:, None] + bed * .16 * duck_bed[:, None]
    # tail fade
    f0 = int(65.6 * SR); mix[f0:] *= np.linspace(1, 0, N - f0)[:, None] ** 1.5
    mix = np.tanh(mix * 1.1) / 1.1
    sf.write(f'{out}/mix_raw.wav', mix.astype(np.float32), SR)
    sf.write(f'{out}/stem_sfx.wav', (sfx * .55).astype(np.float32), SR)
    sf.write(f'{out}/stem_bed.wav', (bed * .16).astype(np.float32), SR)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{out}/mix_raw.wav', '-af',
                    'loudnorm=I=-14:TP=-1.0:LRA=9', '-ar', str(SR), f'{out}/mix.wav'], check=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
