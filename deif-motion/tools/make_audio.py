"""Synthesizes the score and sound effects, then mixes them under the voice-over.

usage: make_audio.py <sfx.json> <voiceover> <duration_s> <out_dir>
writes: mix.wav (final), music.wav, sfx.wav (stems for re-editing)

Everything is generated procedurally (no sample libraries), so the cue times
below follow the shot cue points in scene/main.js."""
import sys, json, subprocess
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

SR = 44100
sfx_events = json.load(open(sys.argv[1]))
VO, DUR, OUT = sys.argv[2], float(sys.argv[3]), sys.argv[4]
N = int(DUR * SR)
rng = np.random.default_rng(3)

def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, a, b, o=2): return sosfilt(butter(o, [a, b], 'band', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(d * SR))
def env(d, a, r, curve=3):
    n = int(d * SR); e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na) ** 2
    e[-nr:] *= np.linspace(1, 0, nr) ** curve
    return e
def expdec(d, tau): return np.exp(-tt(d) / tau)
def saw(f, d, phase=0.0):
    x = (tt(d) * f + phase) % 1.0
    return 2 * x - 1
def place(buf, sig, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf): return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[:len(buf) - i]
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l * 1.41, sig * r * 1.41], 1)
    buf[i:i + len(sig)] += sig * g
def note(n): return 440 * 2 ** ((n - 69) / 12)

def make_ir(d=3.2, damp=2500):
    t = tt(d)
    ir = np.stack([noise(d), noise(d)], 1) * np.exp(-t / (d / 6.5))[:, None]
    ir = np.stack([lp(ir[:, 0], damp), lp(ir[:, 1], damp)], 1)
    return ir / np.abs(ir).sum(0).max() * 6
IR = make_ir()
def reverb(x, wet=.35):
    if x.ndim == 1: x = np.stack([x, x], 1)
    y = np.stack([fftconvolve(x[:, c], IR[:, c])[:len(x)] for c in range(2)], 1)
    return x * (1 - wet) + y * wet

# ---------------- sound effects ----------------
def s_whoosh():
    d = .55; n = noise(d); t = tt(d)
    out = np.zeros_like(n)
    for k, (a, b) in enumerate([(300, 900), (800, 2200), (1800, 4500), (700, 1600)]):
        out += bp(n, a, b) * np.exp(-((t - (.12 + k * .07)) / .09) ** 2)
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    sig = out * e
    pan = np.linspace(-.7, .7, len(sig))
    return np.stack([sig * np.cos((pan + 1) * np.pi / 4), sig * np.sin((pan + 1) * np.pi / 4)], 1) * 1.6
def s_swell():
    d = .5; t = tt(d); n = noise(d)
    sig = bp(n, 400, 5000) * (t / d) ** 3 + np.sin(2 * np.pi * (60 + 200 * (t / d) ** 2) * t) * (t / d) ** 2 * .5
    return reverb(sig * .9, .3)
def s_thud():
    d = .6; t = tt(d)
    body = np.sin(2 * np.pi * (95 * np.exp(-t * 9) + 48) * t) * expdec(d, .16)
    smack = hp(noise(d), 1500) * expdec(d, .012) * .5
    paper = bp(noise(d), 2000, 7000) * expdec(d, .05) * .25
    return reverb(body * 1.2 + smack + paper, .18)
def s_shutter():
    d = .25; t = tt(d); c = hp(noise(d), 2500)
    sig = c * (np.exp(-t / .004) + .8 * np.exp(-np.clip(t - .07, 0, None) / .006) * (t > .07))
    return sig * .8
def s_paper():
    d = .45; t = tt(d); n = bp(noise(d), 1800, 7500)
    flutter = .5 + .5 * np.abs(np.sin(2 * np.pi * 23 * t + 5 * np.sin(2 * np.pi * 3 * t)))
    return n * flutter * env(d, .03, .3) * .55
def s_rip():
    d = .7; t = tt(d); n = bp(noise(d), 900, 6000)
    crackle = (rng.random(len(t)) < .02).astype(float) * rng.uniform(.5, 1, len(t))
    crackle = bp(crackle, 1500, 8000) * 6
    return (n * .5 + crackle) * env(d, .05, .25) * np.clip(t / .5, .3, 1)
def s_tick():
    d = .05; t = tt(d)
    return (np.sin(2 * np.pi * 2300 * t) * .5 + hp(noise(d), 3000) * .6) * expdec(d, .006)
def s_clank():
    d = 1.4; t = tt(d)
    sig = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / dc) for f, a, dc in [(187, .5, .5), (431, .4, .35), (796, .35, .25), (1307, .25, .18), (2011, .15, .1)])
    sig += hp(noise(d), 1000) * expdec(d, .01)
    return reverb(sig * .7, .3)
def s_type():
    d = .06; t = tt(d)
    return (hp(noise(d), 2000) * .7 + np.sin(2 * np.pi * 1100 * t) * .3) * expdec(d, .008)
def s_static():
    d = 1.6; t = tt(d); n = bp(noise(d), 900, 5000) * .35
    crack = (rng.random(len(t)) < .004) * rng.uniform(.4, 1, len(t)); crack = hp(crack, 800) * 3
    hum = np.sin(2 * np.pi * 100 * t) * .05
    return (n + crack + hum) * env(d, .01, .6)
def s_boom():
    d = 3.0; t = tt(d)
    sub = np.sin(2 * np.pi * (60 * np.exp(-t * 3) + 34) * t) * expdec(d, .7)
    hit = lp(noise(d), 600) * expdec(d, .08)
    return reverb(sub * 1.3 + hit * .9, .35)

SFX_FN = dict(whoosh=s_whoosh, swell=s_swell, thud=s_thud, shutter=s_shutter, paper=s_paper, rip=s_rip,
              tick=s_tick, clank=s_clank, type=s_type, static=s_static, boom=s_boom)
SFX_GAIN = dict(whoosh=.30, swell=.30, thud=.42, shutter=.35, paper=.35, rip=.40, tick=.25, clank=.30, type=.30, static=.35, boom=.75)
sfx = np.zeros((N, 2))
cache = {}
seen = set()
for e in sorted(sfx_events, key=lambda e: e['t']):
    key = (e['k'], round(e['t'], 2))
    if key in seen: continue
    seen.add(key)
    sig = SFX_FN[e['k']]() if e['k'] in ('paper', 'rip', 'static', 'whoosh') else cache.setdefault(e['k'], SFX_FN[e['k']]())
    place(sfx, sig, e['t'], SFX_GAIN[e['k']] * e.get('g', 1), pan=rng.uniform(-.25, .25))

# ---------------- score (D minor) ----------------
music = np.zeros((N, 2))
BPM = 84; BEAT = 60 / BPM
CHORDS = [[50, 53, 57, 62], [46, 50, 53, 58], [43, 46, 50, 55], [45, 49, 52, 57]]  # Dm Bb Gm A
def pad(notes, t0, d, g=.06, cut=1100):
    sig = np.zeros(int(d * SR))
    for n in notes:
        for det in (-.07, 0, .06):
            sig += saw(note(n + det), d, rng.random())
    sig = lp(sig, cut, 2) * env(d, min(1.2, d / 3), min(1.6, d / 2), 2) * g
    place(music, reverb(sig, .45), t0)
def drone(t0, d, g=.10):
    t = tt(d)
    sig = (np.sin(2 * np.pi * note(38) * t) + .5 * np.sin(2 * np.pi * note(26) * t) + .25 * lp(saw(note(38), d), 300))
    sig *= (0.8 + 0.2 * np.sin(2 * np.pi * .13 * t)) * env(d, 2, 2.5, 2) * g
    place(music, sig, t0)
def tom(t0, g=.35, f0=110):
    d = .6; t = tt(d)
    s = np.sin(2 * np.pi * (f0 * np.exp(-t * 14) + 46) * t) * expdec(d, .22) + lp(noise(d), 900) * expdec(d, .03) * .4
    place(music, s, t0, g)
def bell(t0, n, g=.07):
    d = 2.2; t = tt(d)
    s = (np.sin(2 * np.pi * note(n) * t) + .3 * np.sin(2 * np.pi * note(n) * 2.01 * t)) * expdec(d, .55)
    place(music, reverb(s, .55), t0, g, pan=rng.uniform(-.6, .6))
def riser(t_end, d=1.8, g=.18):
    t = tt(d)
    s = bp(noise(d), 500, 6000) * (t / d) ** 3 + np.sin(2 * np.pi * (80 + 320 * (t / d) ** 2) * t) * (t / d) ** 2 * .4
    place(music, reverb(s, .3), t_end - d, g)
def heartbeat(t0, g=.4):
    tom(t0, g, 70); tom(t0 + .22, g * .7, 60)

# intro: drone + riser into the title (6.66)
drone(0, 8.8, .09); riser(6.66, 2.2); pad([38, 50, 53, 57], 6.66, 2.4, .05, 700)
# story: pulse + chord cycle
def chords(t0, t1, g, cut):
    k = 0; t = t0
    while t < t1 - .5:
        d = min(8 * BEAT, t1 - t); pad(CHORDS[k % 4], t, d + 1.2, g, cut); k += 1; t += 8 * BEAT
drone(8.4, 45.0, .07)
chords(8.6, 26.18, .045, 900)
chords(26.18, 45.7, .055, 1400)
chords(45.7, 53.14, .05, 1800)
drone(56.2, 15.6, .08)
chords(56.6, 69.88, .05, 1200)
t = 8.6
while t < 69.88:
    if not (53.14 <= t < 56.6):
        strong = 45.7 <= t < 53.14
        tom(t, .21 if strong else .20)
        if strong or 26.18 <= t < 45.7: tom(t + BEAT / 2, .12 if not strong else .13, 140)
    t += BEAT
# bells on the middle section
scale = [62, 65, 67, 69, 72, 74]
t = 26.18; k = 0
while t < 45.7:
    bell(t, scale[(k * 3) % len(scale)], .05); t += BEAT * 1.5; k += 1
riser(47.66, 2.0, .14)
# drop into the shadow (53.14 - 56.6): heartbeat only
for hb in np.arange(53.3, 56.4, .9): heartbeat(hb, .22)
riser(56.6, 1.2, .12)
# ending: final boom + resolving pad
pad([38, 50, 53, 57, 62], 71.7, DUR - 71.7, .06, 900)
fade = np.ones(N); i0 = int((DUR - 2.2) * SR); fade[i0:] = np.linspace(1, 0, N - i0) ** 2
music *= fade[:, None]

# ---------------- mix ----------------
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', VO, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
vo = np.frombuffer(pcm, np.float32).reshape(-1, 2).astype(np.float64)
vo = np.pad(vo, ((0, max(0, N - len(vo))), (0, 0)))[:N]
# duck music under the voice
rms = np.sqrt(lp(np.mean(vo ** 2, 1), 8, 1).clip(0))
duck = 1 - .45 * np.clip(rms / (rms.max() * .25 + 1e-9), 0, 1)
duck = lp(duck, 4, 1)
mus = music * duck[:, None]
mix = vo * 1.0 + mus * 0.9 + sfx * 0.8
peak = np.abs(mix).max(); mix *= .89 / peak
def wav(path, x):
    x = np.clip(x, -1, 1)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', path], input=x.astype(np.float32).tobytes())
wav(f'{OUT}/mix.wav', mix)
wav(f'{OUT}/music.wav', music / (np.abs(music).max() + 1e-9) * .8)
wav(f'{OUT}/sfx.wav', sfx / (np.abs(sfx).max() + 1e-9) * .8)
print('audio ok', len(seen), 'sfx events')
