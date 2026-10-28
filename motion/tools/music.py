"""Original background track (royalty-free, synthesized): 120 bpm, 30 s.
I-V-vi-IV progression, pad + pluck arpeggio + light drums, whooshes on scene cuts."""
import sys, wave
import numpy as np

SR, DUR, BPM = 48000, 30.0, 120
BEAT = 60 / BPM
N = int(SR * DUR)
rng = np.random.default_rng(3)
t_all = np.arange(N) / SR

def lowpass(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / cutoff) ** 4), len(x))

def highpass(x, cutoff):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * (f / cutoff) ** 2 / np.sqrt(1 + (f / cutoff) ** 4), len(x))

def add(buf, start, sig):
    i = int(start * SR)
    if i >= len(buf): return
    sig = sig[: len(buf) - i]; buf[i:i + len(sig)] += sig

def hz(m): return 440 * 2 ** ((m - 69) / 12)

# C  G  Am F  (midi chord tones)
CH = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
BASS = [36, 31, 33, 29]
bar = 4 * BEAT  # 2 s

pad = np.zeros(N); arp = np.zeros(N); bass = np.zeros(N)
kick = np.zeros(N); snare = np.zeros(N); hat = np.zeros(N); fx = np.zeros(N)

nb = int(np.ceil(DUR / bar))
for b in range(nb):
    c = CH[b % 4]; st = b * bar
    n = int(bar * SR * 1.15); tt = np.arange(n) / SR
    env = np.minimum(1, tt / 0.35) * np.exp(-tt * 0.25)
    s = sum(np.sin(2 * np.pi * hz(m + d) * tt) + 0.5 * np.sin(2 * np.pi * 2 * hz(m) * tt + d)
            for m in c for d in (-0.06, 0.0, 0.07))
    add(pad, st, s * env)
    # bass on 1 and the "and" of 3
    for off, ln in ((0, 1.4), (2.5 * BEAT, 0.6)):
        nn = int(ln * SR); tb = np.arange(nn) / SR
        e = np.minimum(1, tb / 0.01) * np.exp(-tb * 2.2)
        add(bass, st + off, (np.sin(2 * np.pi * hz(BASS[b % 4]) * tb) + 0.3 * np.sin(4 * np.pi * hz(BASS[b % 4]) * tb)) * e)
    # 8th-note pluck arpeggio from bar 1
    if st >= 2:
        notes = [c[0] + 12, c[1] + 12, c[2] + 12, c[1] + 24, c[2] + 12, c[0] + 24, c[1] + 12, c[2] + 12]
        for k, m in enumerate(notes):
            nn = int(0.45 * SR); tp = np.arange(nn) / SR
            e = np.minimum(1, tp / 0.004) * np.exp(-tp * 9)
            add(arp, st + k * BEAT / 2, (np.sin(2 * np.pi * hz(m) * tp) + 0.25 * np.sin(6 * np.pi * hz(m) * tp)) * e * (0.8 if k % 2 else 1))

drums_on = lambda x: 2.0 <= x < 26.0
for k in range(int(DUR / BEAT)):
    x = k * BEAT
    if drums_on(x):
        nn = int(0.35 * SR); tk = np.arange(nn) / SR
        f = 50 + 110 * np.exp(-tk * 35)
        add(kick, x, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk * 9))
        if x >= 6 and k % 4 in (1, 3):
            nn = int(0.25 * SR); ts = np.arange(nn) / SR
            add(snare, x, rng.standard_normal(nn) * np.exp(-ts * 18) + 0.4 * np.sin(2 * np.pi * 190 * ts) * np.exp(-ts * 25))
    if 4 <= x < 26:
        for h in (0.5, ):  # off-beat hats
            nn = int(0.06 * SR); th = np.arange(nn) / SR
            add(hat, x + h * BEAT, rng.standard_normal(nn) * np.exp(-th * 70))

# whooshes leading into each scene cut
for cut in (3, 6, 9, 13, 16, 20, 23, 26):
    ln = 0.6; nn = int(ln * SR); tw = np.arange(nn) / SR
    nz = highpass(rng.standard_normal(nn), 1500)
    add(fx, cut - ln + 0.08, nz * (tw / ln) ** 2 * np.exp(-np.maximum(0, tw - ln + .1) * 30))
# impacts: stamp (17.0) and end card (26.0)
for hit, g in ((17.0, 1.0), (26.0, 0.8)):
    nn = int(1.6 * SR); ti = np.arange(nn) / SR
    boom = np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-ti * 12)) / SR) * np.exp(-ti * 3)
    add(fx, hit, g * (boom * 1.2 + lowpass(rng.standard_normal(nn), 3000) * np.exp(-ti * 10) * .4))

pad = lowpass(pad, 1800)
hat = highpass(hat, 7000)
snare = highpass(snare, 900)
mix_m = 0.11 * pad + 0.5 * bass + 0.16 * arp + 0.9 * kick + 0.22 * snare + 0.12 * hat + 0.3 * fx

# stereo: arp & hats ping-pong slightly, pad widened with a short delay
d = int(0.012 * SR)
L = mix_m + 0.05 * np.roll(arp, d) + 0.03 * np.roll(pad, d)
R = mix_m + 0.05 * np.roll(arp, 2 * d) + 0.03 * np.roll(pad, 2 * d)
# soft sidechain-ish pump on the pad under the kick
st = np.stack([L, R], 1)
# master: fade in 0.3 s, fade out over last 3 s, tanh glue, normalize
fade = np.minimum(1, t_all / 0.3) * np.clip((DUR - t_all) / 3.0, 0, 1) ** 1.5
st = np.tanh(st * fade[:, None] * 0.8)
st = st / np.abs(st).max() * 0.89
pcm = (st * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', sys.argv[1])
