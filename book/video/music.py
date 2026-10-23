#!/usr/bin/env python3
"""Composes the trailer's score from code: soft piano, a pad, wind, an ice crack and a heartbeat,
laid out on the trailer's scene timeline (see SCENES). Original music, no samples.

Writes video/build/score.wav (44.1 kHz stereo).
Usage: python3 video/music.py
"""
from pathlib import Path

import numpy as np

SR = 44100
LENGTH = 94.0
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"

# scene starts in seconds, matching the voice-over script
SCENES = {"open": 0, "near": 8, "home": 22, "shock": 30, "mark": 42, "questions": 52,
          "confess": 62, "open_end": 72, "title": 82}

rng = np.random.default_rng(11)


def n(name):
    """Note name like 'A3' or 'C#4' to frequency."""
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    pitch = names[name[0]]
    rest = name[1:]
    if rest.startswith("#"):
        pitch += 1
        rest = rest[1:]
    elif rest.startswith("b"):
        pitch -= 1
        rest = rest[1:]
    midi = 12 * (int(rest) + 1) + pitch
    return 440.0 * 2 ** ((midi - 69) / 12)


class Track:
    def __init__(self, length=LENGTH):
        self.buf = np.zeros((int(length * SR), 2), np.float32)

    def add(self, start, mono, pan=0.0, gain=1.0):
        i = int(start * SR)
        if i >= len(self.buf):
            return
        seg = mono[: len(self.buf) - i] * gain
        left, right = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.buf[i:i + len(seg), 0] += seg * left
        self.buf[i:i + len(seg), 1] += seg * right


def piano(freq, dur=5.0, vel=0.6):
    """A soft piano-like tone: a few slightly stretched partials, a felt hammer, a long decay."""
    t = np.arange(int(dur * SR)) / SR
    tone = np.zeros_like(t)
    decay = 1.6 + 220 / freq  # low notes ring longer
    for k, amp in enumerate([1.0, 0.42, 0.22, 0.12, 0.07, 0.04], start=1):
        f = freq * k * (1 + 0.0004 * k * k)
        if f > 9000:
            break
        tone += amp * np.sin(2 * np.pi * f * t + rng.random() * 6.28) * np.exp(-t * k * 0.9 / decay)
    attack = np.clip(t / 0.006, 0, 1)
    body = np.exp(-t / decay) * 0.85 + 0.15 * np.exp(-t / 0.25)
    hammer = rng.normal(0, 1, len(t)) * np.exp(-t / 0.004) * 0.05
    fade = np.clip((dur - t) / 0.4, 0, 1)
    return ((tone * body * attack + hammer) * fade * vel * 0.32).astype(np.float32)


def pad(freqs, dur, gain=0.05, swell=3.0):
    """A slow, breathing pad of detuned sines."""
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.0, 0.13):
            ff = f * (1 + det / 100)
            out += np.sin(2 * np.pi * ff * t + rng.random() * 6.28)
            out += 0.18 * np.sin(2 * np.pi * 2 * ff * t)
    env = np.minimum(np.clip(t / swell, 0, 1), np.clip((dur - t) / swell, 0, 1)) ** 1.5
    lfo = 1 + 0.12 * np.sin(2 * np.pi * 0.13 * t)
    return (out * env * lfo * gain / (len(freqs) * 3)).astype(np.float32)


def band_noise(dur, lo, hi, gain):
    x = rng.normal(0, 1, int(dur * SR))
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= np.exp(-((np.log(f + 1) - np.log((lo * hi) ** 0.5)) / np.log(hi / lo) * 2.2) ** 2)
    y = np.fft.irfft(spec, len(x))
    return (y / (np.abs(y).max() + 1e-9) * gain).astype(np.float32)


def wind(dur, gain=0.05):
    w = band_noise(dur, 250, 1400, 1.0)
    t = np.arange(len(w)) / SR
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.07 * t + 1) * np.sin(2 * np.pi * 0.031 * t)
    env = np.minimum(np.clip(t / 3, 0, 1), np.clip((dur - t) / 3, 0, 1))
    return (w * gust * env * gain).astype(np.float32)


def ice_crack():
    """A sharp crack splitting into smaller ones, and a low thud under it."""
    dur = 2.6
    out = np.zeros(int(dur * SR), np.float32)
    t = np.arange(len(out)) / SR
    hits = [0.0, 0.05, 0.11, 0.19, 0.32, 0.5, 0.74, 1.05]
    for i, h in enumerate(hits):
        L = int(0.09 * SR)
        burst = rng.normal(0, 1, L) * np.exp(-np.arange(L) / SR / (0.012 + 0.004 * i))
        k = int(h * SR)
        out[k:k + L] += burst * (0.9 ** i)
    spec = np.fft.rfft(out)
    f = np.fft.rfftfreq(len(out), 1 / SR)
    spec *= np.clip(f / 900, 0, 1) * np.exp(-f / 7000)
    crack = np.fft.irfft(spec, len(out))
    crack = crack / (np.abs(crack).max() + 1e-9) * 0.55
    thud = np.sin(2 * np.pi * (55 * np.exp(-t * 3)) * t) * np.exp(-t / 0.35) * 0.45
    return (crack + thud).astype(np.float32)


def heartbeat(gain=0.35):
    t = np.arange(int(0.9 * SR)) / SR
    def thump(t0, a):
        tt = np.clip(t - t0, 0, None)
        return a * np.sin(2 * np.pi * 52 * tt) * np.exp(-tt / 0.07) * (t >= t0)
    return ((thump(0, 1.0) + thump(0.24, 0.7)) * gain).astype(np.float32)


def reverb(stereo, seconds=3.2, wet=0.32):
    """Convolution with a synthetic hall: decaying, darkening noise, different per channel."""
    L = int(seconds * SR)
    t = np.arange(L) / SR
    out = np.empty_like(stereo)
    size = 1 << int(np.ceil(np.log2(len(stereo) + L)))
    for c in range(2):
        ir = rng.normal(0, 1, L) * np.exp(-t / (seconds / 6.5))
        spec = np.fft.rfft(ir)
        f = np.fft.rfftfreq(L, 1 / SR)
        spec *= np.exp(-f / 4500)
        ir = np.fft.irfft(spec, L)
        ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
        ir /= np.sqrt((ir ** 2).sum())
        y = np.fft.irfft(np.fft.rfft(stereo[:, c], size) * np.fft.rfft(ir, size), size)[: len(stereo)]
        out[:, c] = stereo[:, c] * (1 - wet) + y * wet * 2.2
    return out


CHORDS = {
    "Am": ["A2", "E3", "A3", "C4", "E4"],
    "F": ["F2", "C3", "F3", "A3", "C4"],
    "C": ["C3", "G3", "C4", "E4", "G4"],
    "G": ["G2", "D3", "G3", "B3", "D4"],
    "Fmaj7": ["F2", "C3", "E3", "A3", "E4"],
    "Gsus": ["G2", "D3", "G3", "C4", "D4"],
    "Am9": ["A2", "E3", "B3", "C4", "E4"],
    "Dm": ["D3", "A3", "D4", "F4"],
}


def arpeggio(track, start, chord, beats=4, beat=0.909, vel=0.5, pattern=(0, 1, 2, 3)):
    notes = CHORDS[chord]
    for b in range(beats):
        idx = pattern[b % len(pattern)]
        f = n(notes[idx])
        track.add(start + b * beat + rng.normal(0, 0.006), piano(f, 5.5, vel * (1.0 if b == 0 else 0.8)),
                  pan=-0.25 + 0.15 * idx)


def compose():
    s = SCENES
    piano_t, pad_t, fx_t = Track(), Track(), Track()
    beat = 60 / 66

    # 1. open: wind, a held low pad, a few single notes like a screen lighting up
    fx_t.add(0, wind(31, 0.06))
    pad_t.add(0.5, pad([n("A2"), n("E3")], 9, 0.05, 3))
    for t0, nn in [(2.2, "E5"), (4.6, "A4"), (6.4, "C5")]:
        piano_t.add(t0, piano(n(nn), 6, 0.35), pan=0.2)

    # 2–3. near, home: warm arpeggios, a small melody above
    prog = ["Am", "F", "C", "G", "Am", "F"]
    t = s["near"]
    for ch in prog:
        arpeggio(piano_t, t, ch, beats=4, beat=beat, vel=0.42)
        pad_t.add(t, pad([n(x) for x in CHORDS[ch][:3]], 4 * beat + 1.2, 0.045, 1.2))
        t += 4 * beat
    melody = [(s["near"] + 3.6, "E5"), (s["near"] + 5.4, "D5"), (s["near"] + 7.3, "C5"),
              (s["near"] + 10.9, "G5"), (s["near"] + 12.7, "E5"), (s["near"] + 14.5, "D5"),
              (s["home"] + 0.2, "C5"), (s["home"] + 1.9, "E5"), (s["home"] + 4.0, "A5"),
              (s["home"] + 6.2, "G5")]
    for t0, nn in melody:
        piano_t.add(t0, piano(n(nn), 6, 0.33), pan=0.15)

    # 4. shock: everything stops; the ice cracks; a low, uneasy drone
    fx_t.add(s["shock"] + 0.2, ice_crack(), pan=0.0, gain=1.0)
    pad_t.add(s["shock"] + 1.2, pad([n("A1"), n("Bb2"), n("E3")], 11.5, 0.05, 2.5))
    piano_t.add(s["shock"] + 4.5, piano(n("A1"), 7, 0.5))
    piano_t.add(s["shock"] + 8.0, piano(n("Bb3"), 5, 0.22), pan=-0.3)

    # 5. the mark it leaves: single low notes, the warmth not quite back
    for i, (nn, v) in enumerate([("A2", 0.4), ("E3", 0.3), ("C4", 0.28), ("B3", 0.26), ("A3", 0.3)]):
        piano_t.add(s["mark"] + 0.4 + i * 1.9, piano(n(nn), 6, v), pan=-0.2 + 0.1 * i)
    pad_t.add(s["mark"], pad([n("A2"), n("E3"), n("C4")], 10.5, 0.04, 3))

    # 6. questions: a heartbeat, a repeated high note like a thought that won't stop
    for k in range(13):
        fx_t.add(s["questions"] + k * 0.78, heartbeat(0.32 + 0.02 * k))
    for k in range(20):
        piano_t.add(s["questions"] + 0.4 + k * 0.48, piano(n("E5" if k % 4 else "F5"), 2.5, 0.16 + 0.006 * k), pan=0.35)
    pad_t.add(s["questions"], pad([n("D3"), n("F3"), n("A3")], 10.5, 0.05, 2))

    # 7. confession: slow chords, very quiet
    for i, ch in enumerate(["F", "C", "Am", "G"]):
        t0 = s["confess"] + 0.3 + i * 2.5
        for j, nn in enumerate(CHORDS[ch][1:]):
            piano_t.add(t0 + j * 0.03, piano(n(nn), 6, 0.3))
        pad_t.add(t0, pad([n(x) for x in CHORDS[ch][:3]], 3.6, 0.035, 1.0))

    # 8. the open ending: suspended chords that don't resolve
    for i, ch in enumerate(["Fmaj7", "Gsus", "Fmaj7", "Gsus"]):
        t0 = s["open_end"] + i * 2.5
        for j, nn in enumerate(CHORDS[ch]):
            piano_t.add(t0 + j * 0.12, piano(n(nn), 6, 0.27), pan=-0.2 + 0.1 * j)
    pad_t.add(s["open_end"], pad([n("F2"), n("C3"), n("G3")], 10.5, 0.045, 3))
    fx_t.add(s["open_end"], wind(LENGTH - s["open_end"], 0.045))

    # 9. title: a few high notes, and a last chord left open
    for t0, nn in [(s["title"] + 0.5, "E5"), (s["title"] + 1.6, "B4"), (s["title"] + 2.8, "C5")]:
        piano_t.add(t0, piano(n(nn), 6, 0.3), pan=0.1)
    for j, nn in enumerate(CHORDS["Am9"]):
        piano_t.add(s["title"] + 4.2 + j * 0.09, piano(n(nn), 8, 0.32), pan=-0.2 + 0.1 * j)
    pad_t.add(s["title"] + 3.5, pad([n("A2"), n("E3"), n("B3")], LENGTH - s["title"] - 3.5, 0.045, 3))

    music = reverb(piano_t.buf, 3.4, 0.35) + reverb(pad_t.buf, 4.0, 0.45)
    # the silence around the crack: the music drops away while the crack stays on top
    t = np.arange(len(music)) / SR
    duck = 1 - 0.85 * np.exp(-((t - (s["shock"] + 0.6)) / 0.9) ** 2) * (t > s["shock"] - 0.3)
    mix = music * duck[:, None] ** 0.6 + fx_t.buf
    fade = np.clip((LENGTH - t) / 4.0, 0, 1)[:, None]
    mix *= fade
    mix /= np.abs(mix).max() + 1e-9
    return (mix * 0.89).astype(np.float32)


def write_wav(path, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write_wav(OUT / "score.wav", compose())
    print("wrote", OUT / "score.wav")


if __name__ == "__main__":
    main()
