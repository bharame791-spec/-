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

# scene starts in seconds; the trailer's make.py sets these from the voice-over's timing
SCENES = {"open": 0, "near": 8, "home": 22, "pre": 26, "shock": 30, "mark": 42, "questions": 52,
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
    """Lays the score on SCENES (scene starts in seconds) over LENGTH seconds."""
    s = SCENES
    piano_t, pad_t, fx_t = Track(LENGTH), Track(LENGTH), Track(LENGTH)
    beat = 60 / 66

    def span(a, b):
        return s[b] - s[a]

    # 1. open: wind, a held low pad, a few single notes like a screen lighting up
    fx_t.add(0, wind(s["shock"] + 1, 0.06))
    pad_t.add(0.3, pad([n("A2"), n("E3")], s["near"] + 1.5, 0.05, 2.5))
    for frac, nn in [(0.22, "E5"), (0.5, "A4"), (0.75, "C5")]:
        piano_t.add(s["near"] * frac, piano(n(nn), 6, 0.35), pan=0.2)

    # 2–3. near, home: warm arpeggios with a small melody, until the word that hurt
    chords = ["Am", "F", "C", "G", "Am", "F", "C", "G"]
    count = max(1, int(span("near", "pre") // (4 * beat)))
    t = s["near"]
    for ch in chords[:count]:
        arpeggio(piano_t, t, ch, beats=4, beat=beat, vel=0.42)
        pad_t.add(t, pad([n(x) for x in CHORDS[ch][:3]], 4 * beat + 1.2, 0.045, 1.2))
        t += 4 * beat
    tune = ["E5", "D5", "C5", "G5", "E5", "D5", "C5", "E5", "A5", "G5"]
    for i, nn in enumerate(tune):
        t0 = s["near"] + 3.6 + i * (count * 4 * beat - 4.5) / len(tune)
        piano_t.add(t0, piano(n(nn), 6, 0.33), pan=0.15)

    # the word that hurt: the warmth drains to one held, uneasy chord
    pad_t.add(s["pre"], pad([n("A2"), n("E3"), n("Bb3")], span("pre", "shock") + 0.6, 0.05, 1.5))
    piano_t.add(s["pre"] + 0.4, piano(n("A2"), 6, 0.35))

    # 4. shock: everything stops; the ice cracks; a low drone
    fx_t.add(s["shock"], ice_crack(), pan=0.0, gain=1.0)
    pad_t.add(s["shock"] + 1.0, pad([n("A1"), n("Bb2"), n("E3")], span("shock", "mark") + 1.0, 0.05, 1.5))
    piano_t.add(s["shock"] + 1.6, piano(n("A1"), 6, 0.45))

    # 5. the mark it leaves: single low notes, the warmth not quite back
    notes = [("A2", 0.4), ("E3", 0.3), ("C4", 0.28), ("B3", 0.26), ("A3", 0.3)]
    gap = (span("mark", "questions") - 0.6) / len(notes)
    for i, (nn, v) in enumerate(notes):
        piano_t.add(s["mark"] + 0.3 + i * gap, piano(n(nn), 6, v), pan=-0.2 + 0.1 * i)
    pad_t.add(s["mark"], pad([n("A2"), n("E3"), n("C4")], span("mark", "questions") + 0.5, 0.04, 2))

    # 6. questions: a heartbeat, a repeated high note like a thought that won't stop
    for t0 in heartbeat_times():
        fx_t.add(t0, heartbeat(0.32 + 0.02 * (t0 - s["questions"])))
    k = 0
    while s["questions"] + 0.4 + k * 0.48 < s["confess"] - 1.0:
        piano_t.add(s["questions"] + 0.4 + k * 0.48, piano(n("E5" if k % 4 else "F5"), 2.5, 0.16 + 0.006 * k), pan=0.35)
        k += 1
    pad_t.add(s["questions"], pad([n("D3"), n("F3"), n("A3")], span("questions", "confess") + 0.5, 0.05, 2))

    # 7. confession: slow chords, very quiet
    step = span("confess", "open_end") / 4
    for i, ch in enumerate(["F", "C", "Am", "G"]):
        t0 = s["confess"] + 0.3 + i * step
        for j, nn in enumerate(CHORDS[ch][1:]):
            piano_t.add(t0 + j * 0.03, piano(n(nn), 6, 0.3))
        pad_t.add(t0, pad([n(x) for x in CHORDS[ch][:3]], step + 1.1, 0.035, 1.0))

    # 8. the open ending: suspended chords that don't resolve
    step = span("open_end", "title") / 4
    for i, ch in enumerate(["Fmaj7", "Gsus", "Fmaj7", "Gsus"]):
        t0 = s["open_end"] + i * step
        for j, nn in enumerate(CHORDS[ch]):
            piano_t.add(t0 + j * 0.12, piano(n(nn), 6, 0.27), pan=-0.2 + 0.1 * j)
    pad_t.add(s["open_end"], pad([n("F2"), n("C3"), n("G3")], span("open_end", "title") + 0.5, 0.045, 2.5))
    fx_t.add(s["open_end"], wind(LENGTH - s["open_end"], 0.045))

    # 9. title: a few high notes, and a last chord left open
    for d, nn in [(0.0, "E5"), (0.85, "B4"), (1.9, "C5")]:
        piano_t.add(s["title"] + d, piano(n(nn), 6, 0.3), pan=0.1)
    for j, nn in enumerate(CHORDS["Am9"]):
        piano_t.add(s["title"] + 3.0 + j * 0.09, piano(n(nn), 8, 0.32), pan=-0.2 + 0.1 * j)
    pad_t.add(s["title"] + 2.5, pad([n("A2"), n("E3"), n("B3")], LENGTH - s["title"] - 2.5, 0.045, 2.5))

    music = reverb(piano_t.buf, 3.4, 0.35) + reverb(pad_t.buf, 4.0, 0.45)
    # the silence around the crack: the music drops away while the crack stays on top
    t = np.arange(len(music)) / SR
    duck = 1 - 0.85 * np.exp(-((t - (s["shock"] + 0.4)) / 0.9) ** 2) * (t > s["shock"] - 0.3)
    mix = music * duck[:, None] ** 0.6 + fx_t.buf
    fade = np.clip((LENGTH - t) / 3.0, 0, 1)[:, None]
    mix *= fade
    mix /= np.abs(mix).max() + 1e-9
    return (mix * 0.89).astype(np.float32)


def heartbeat_times():
    """When the heartbeat falls during the questions (the trailer pulses on the same beats)."""
    times, t0 = [], SCENES["questions"]
    while t0 < SCENES["confess"] - 0.8:
        times.append(round(t0, 3))
        t0 += 0.78
    return times


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
