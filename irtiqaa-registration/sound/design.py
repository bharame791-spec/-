"""Sound design + mix for the Irtiqaa registration video.

All SFX are synthesised here (modal metal, Karplus-Strong plucks, granular sand/paper,
spectrally-shaped noise whooshes, convolution reverb) and placed on the exact animation
timestamps from index.html. Output: mix.wav (VO + SFX only, no music, loudness-ready).
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

# ------------------------------------------------------------------ SCORE (minimal, no tonal/bell sounds)
def io(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

# S1 gate
place(click(.08, 1450, 45, 180, 1.0, .9), 1.55, .35, send=.3)                            # latch
place(sub_hit(3.0, 64, 30, 1.8, .15, .7), 1.6, .50, send=.3)                              # heavy gate
place(whoosh(1.6, 180, 900, 300, .55, 1.0, (-.6, .6), .15), 1.6, .30, send=.25)            # doors swing
place(whoosh(1.5, 250, 2600, 800, .6, 1.0, (.3, -.2)), 3.45, .30)                          # camera up
# S2 board
place(sub_hit(.6, 140, 80, 9, .3, .6), 4.55, .22, send=.1)
for t0 in [5.0, 5.15, 5.3, 5.52, 5.72, 5.92]:
    place(flap_flurry(rng.integers(5, 8), .2), t0, .30, pan=rng.uniform(-.2, .2), send=.1)
# S3 ticket
place(whoosh(1.7, 900, 2000, 300, .45, 1.0, (.2, -.3)), 6.5, .26)                          # camera down
place(paper(1.6, (1200, 5000), 700) * smooth_env(int(1.6 * SR), [(0, 0), (.15, 1), (.85, .7), (1, 0)]), 7.1, .18, send=.1)
place(whoosh(.9, 700, 3500, 1500, .7, .8, (.7, 0), .2), 19.25, .18)
place(modal([2480, 3710, 5120], [.03, .02, .012], [1, .6, .4], .1), 20.1, .30, send=.15)  # punch
place(sub_hit(.5, 160, 90, 14, .4, .5), 20.1, .35, send=.15)
riser = shaped(2.3, lambda u: 300 * (6000 / 300) ** (u ** 1.4), lambda u: 1.1) * np.linspace(0, 1, int(2.3 * SR)) ** 2.8
place(pan2(norm(riser), 0), 19.45, .25, send=.4)
place(sub_hit(3.5, 52, 28, 1.3, .05, .4), 21.72, .40, send=.5)                           # into the light
# S4 stations
for k in range(1, 5):
    place(whoosh(1.25, 220, 2300, 700, .55, 1.05, (.5, -.5), .2), TS[k] - .2, .26)
T = TS[0]
place(paper(.25, (1100, 4500), 1500), T + 1.6, .20, send=.2)
place(sub_hit(.9, 120, 60, 7, .5, 1.0), T + 3.65, .45, send=.25)                         # stamp
place(click(.05, 900, 60, 140, 1.0, .6), T + 3.65, .25, send=.15)
T = TS[1]
place(sub_hit(2.0, 75, 38, 2.2, .05, .3), T + 1.0, .22, send=.4)                          # alif
wd = 3.1; wind = shaped(wd, lambda u: 380 + 380 * np.sin(u * 7) ** 2 + 300 * u, lambda u: .75)
we = smooth_env(int(wd * SR), [(0, 0), (.18, .8), (.35, 1), (.55, .85), (.75, .35), (1, 0)])
place(norm(np.stack([wind * we, np.roll(wind, 2400) * we], 1)), T + 1.45, .30, send=.3)
T = TS[2]
place(pan2(norm(shaped(1.0, lambda u: 1300, lambda u: 1.3) * env_ar(int(SR), .35, .65)), 0), T + .65, .12, send=.15)
for j in range(9):
    f = .06 + .1 * j; lo, hi = 0.0, 1.0
    for _ in range(40):
        m = (lo + hi) / 2
        if io(m) < f + .02: lo = m
        else: hi = m
    place(footstep_sand(1 - .06 * j), T + 1.6 + 2.0 * lo, .26 * (1 - .05 * j), pan=(-.2 if j % 2 else .2), send=.15)
T = TS[3]
place(drop_plop(), T + 2.25, .35, send=.6)                                                 # water drop
T = TS[4]
place(sub_hit(.9, 100, 55, 5, .1, .9), T + .6, .16, send=.15)                             # ground
for i in range(6): place(paper(.08, (2000, 6000), 2500), T + 2.66 + .18 * i, .07, send=.15)
# S5 reveal
place(whoosh(1.4, 1500, 400, 120, .2, 1.2, (-.5, .5), .3), 44.95, .30)                     # pull back
place(reverse_swell(.75, (600, 6000)), 45.75, .25, send=.3)
place(sub_hit(4.0, 60, 28, 1.0, .4, 1.0), 46.45, .60, send=.5)                            # logo hit
for i, st in enumerate([49.1, 50.55, 51.75, 53.05]):
    place(modal([690, 1810], [.04, .02], [1, .4], .15), st + .33, .16, pan=(.3 if i % 2 == 0 else -.3), send=.2)
# S6 ticket flip / QR
place(whoosh(1.0, 300, 1800, 600, .55, 1.0, (-.2, .2)), 53.95, .26)
place(whoosh(.85, 900, 3500, 1200, .55, .7, (.6, -.6), .3), 55.2, .28)
place(paper(.12, (2000, 6000), 3000), 55.95, .18, send=.15)
place(whoosh(.8, 500, 2600, 1300, .6, 1.0, (0, 0)), 59.5, .24)
# S7 end card
place(sub_hit(.8, 130, 70, 8, .4, .9), 60.28, .28, send=.15)
for t0 in [60.1, 60.45]: place(flap_flurry(7, .22), t0, .30, send=.1)
place(sub_hit(4.0, 58, 28, .9, .2, .8), 64.1, .45, send=.6)                               # final hit

# ------------------------------------------------------------------ mix
def main(vo_path, out):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', vo_path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    vo = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    V = np.zeros((N, 2)); i = int(VO_OFFSET * SR); V[i:i + len(vo)] = vo[:N - i]
    ir = make_ir()
    sfx = B['dry'] + convolve_st(B['send'], ir) * .55
    # VO-driven ducking
    lvl = np.sqrt(np.convolve(V.mean(1) ** 2, np.ones(2400) / 2400, 'same'))
    on = (lvl > .02).astype(float)
    k = int(.25 * SR); on = np.convolve(on, np.ones(k) / k, 'same')
    duck_bed = 1 - .45 * np.clip(on, 0, 1); duck_sfx = 1 - .40 * np.clip(on, 0, 1)
    vo_g = 10 ** (0 / 20)
    mix = V * vo_g + sfx * .40 * duck_sfx[:, None]
    # tail fade
    f0 = int(65.6 * SR); mix[f0:] *= np.linspace(1, 0, N - f0)[:, None] ** 1.5
    mix = np.tanh(mix * 1.1) / 1.1
    sf.write(f'{out}/mix_raw.wav', mix.astype(np.float32), SR)
    sf.write(f'{out}/stem_sfx.wav', (sfx * .40).astype(np.float32), SR)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{out}/mix_raw.wav', '-af',
                    'loudnorm=I=-14:TP=-2.0:LRA=9', '-ar', str(SR), f'{out}/mix.wav'], check=True)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
