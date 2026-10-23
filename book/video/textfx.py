#!/usr/bin/env python3
"""Masks for the trailer's words: a bristly brush edge that paints them on (right to left),
and a sequence of dissolve masks that let them evaporate like ink into fog.

Writes video/build/art/sweep.png and dissolve0.png ... dissolve11.png.
Usage: python3 video/textfx.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import illustrate as I  # noqa: E402

OUT = HERE / "build" / "art"
STEPS = 12


def sweep(w=3000, h=400, seed=3):
    """Opaque on the right, clear on the left; between them the edge of a dry brush: every row
    (a bristle) reaches a little further or falls a little short, with gaps where the paint ran thin."""
    rng = np.random.default_rng(seed)
    xs = np.arange(w)[None, :].astype(np.float32)
    rows = I.smooth_noise(1, h, 6, rng)[:, 0] * 0.6 + rng.normal(0, 1, h) * 0.5
    edge = (0.5 + rows * 0.035)[:, None] * w            # where each bristle's paint ends
    soft = 0.012 * w
    a = np.clip((xs - (edge - soft)) / (2 * soft), 0, 1)  # 0 left of the edge, 1 right of it
    # dry streaks just behind the edge
    streak = np.clip(I.smooth_noise(w, h, 4, rng) * 0.5 + 0.5, 0, 1)
    behind = np.clip((xs - edge) / (0.05 * w), 0, 1)
    a *= np.clip(1 - (1 - behind) * (streak < 0.35) * 0.9, 0, 1)
    img = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    Image.merge("RGBA", [Image.new("L", (w, h), 0)] * 3 + [img]).save(OUT / "sweep.png", optimize=True)


def dissolves(w=1200, h=300, seed=4):
    """Ink evaporating: holes open in a cloudy pattern until nothing is left."""
    rng = np.random.default_rng(seed)
    field = I.smooth_noise(w, h, 26, rng) * 0.6 + I.smooth_noise(w, h, 6, rng) * 0.4
    field = (field - field.min()) / (field.max() - field.min())
    for k in range(STEPS):
        thr = k / (STEPS - 1) * 1.05
        a = np.clip((field - thr) / 0.06 + 1, 0, 1) if k else np.ones_like(field)
        img = Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
        Image.merge("RGBA", [Image.new("L", (w, h), 0)] * 3 + [img]).save(OUT / f"dissolve{k}.png", optimize=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sweep()
    dissolves()
    print("wrote text masks into", OUT)


if __name__ == "__main__":
    main()
