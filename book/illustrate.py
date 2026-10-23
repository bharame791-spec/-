#!/usr/bin/env python3
"""Draws the book's artwork: paper textures and the cover's window of dim light.

Everything is generated from code (no external images). Writes into ./art:
  paper.jpg / paper.pdf    warm paper (#EDE5D9) for the text pages
  ivory.jpg / ivory.pdf    ivory (#F7F4EE) for the title and dedication pages
  navy.jpg                 deep navy (#17263B) with a light paper grain, for dark pages
  cover.jpg                front cover: navy, a half-dark window letting in faint light
  back.jpg                 back cover: navy, a small echo of the window

Usage: python3 illustrate.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
ART = ROOT / "art"

W, H = 1600, 2270  # A5 at ~275 dpi

NAVY = (23, 38, 59)       # #17263B
PAPER = (237, 229, 217)   # #EDE5D9
IVORY = (247, 244, 238)   # #F7F4EE
FOG = (167, 167, 160)     # #A7A7A0


def smooth_noise(w, h, cell, rng):
    small = rng.random((max(2, h // cell + 2), max(2, w // cell + 2))).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(cell / 3))
    a = np.asarray(img, np.float32) / 255.0
    return (a - a.mean()) / (a.std() + 1e-6)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def specks(w, h, rng, per_px, rmin, rmax):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for _ in range(int(w * h * per_px)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(rmin, rmax)
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(60, 200)))
    return np.asarray(m.filter(ImageFilter.GaussianBlur(0.5)), np.float32)[..., None] / 255.0


def textured(w, h, base, seed, grain=3.0, mottle=2.4, dark_specks=0.0, light_specks=0.0, edge=0.05):
    """A sheet of paper in the given colour: mottling, tooth, flecks, slightly aged edges."""
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    img += smooth_noise(w, h, 380, rng)[..., None] * mottle
    img += smooth_noise(w, h, 40, rng)[..., None] * mottle * 0.5
    img += rng.normal(0, grain, (h, w, 1)).astype(np.float32)
    if dark_specks:
        f = specks(w, h, rng, dark_specks, 0.5, 1.3)
        img = img * (1 - 0.3 * f) + np.array([130, 120, 108], np.float32) * 0.3 * f
    if light_specks:
        f = specks(w, h, rng, light_specks, 0.5, 1.2)
        img = img * (1 - 0.25 * f) + np.array([250, 248, 242], np.float32) * 0.25 * f
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    img *= (1 + edge * 0.3 - edge * smoothstep(0.4, 1.45, r))[..., None]
    return img


def navy_sheet(seed):
    return textured(W, H, NAVY, seed, grain=2.2, mottle=1.6, light_specks=1 / 5000, edge=0.18)


def window(img, cx, top, ww, wh, strength=1.0, floor=True):
    """A plain four-pane window on a dark wall, letting in faint light that falls on the floor."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    left, right, bottom = cx - ww / 2, cx + ww / 2, top + wh
    fog = np.array(FOG, np.float32)
    ivory = np.array(IVORY, np.float32)

    # the wall around the window turns slowly from navy to fog grey
    d = np.sqrt(((xx - cx) / (ww * 2.1)) ** 2 + ((yy - (top + wh * 0.45)) / (wh * 1.5)) ** 2)
    halo = np.exp(-d ** 2 * 1.6)[..., None] * 0.28 * strength
    img[:] = img * (1 - halo) + fog * halo

    if floor:
        # light thrown onto the floor toward the viewer: a widening, fading trapezoid
        m = Image.new("L", (w, h), 0)
        dr = ImageDraw.Draw(m)
        spread = ww * 0.95
        dr.polygon([(left + ww * 0.06, bottom + h * 0.012), (right - ww * 0.06, bottom + h * 0.012),
                    (right + spread, h * 0.985), (left - spread, h * 0.985)], fill=255)
        mask = np.asarray(m.filter(ImageFilter.GaussianBlur(ww * 0.09)), np.float32) / 255.0
        fade = (1 - smoothstep(bottom, h * 1.02, yy)) ** 1.4
        # the mullion's shadow runs through the patch of light
        mull = 1 - 0.55 * np.exp(-((xx - cx) / (ww * 0.035 + np.clip(yy - bottom, 0, None) * 0.02)) ** 2)
        a = (mask * fade * mull)[..., None] * 0.20 * strength
        img[:] = img * (1 - a) + fog * a
        # the line where the far wall meets the floor
        line = np.exp(-((yy - bottom - h * 0.012) / 3.0) ** 2)[..., None] * 0.10 * np.clip(halo * 4, 0, 1)
        img[:] = img * (1 - line)

    # the glass: dim light, brighter toward the top, a little haze
    glass = (xx > left) & (xx < right) & (yy > top) & (yy < bottom)
    t = np.clip((yy - top) / wh, 0, 1)[..., None]
    rng = np.random.default_rng(3)
    light = (fog * 0.55 + ivory * 0.45) * (1 - t * 0.45) + smooth_noise(w, h, 90, rng)[..., None] * 3
    k = 0.72 * strength
    img[glass] = img[glass] * (1 - k) + light[glass] * k

    # frame and mullions in the colour of the night
    m = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(m)
    fw = max(3, int(ww * 0.035))
    dr.rectangle([left, top, right, bottom], outline=255, width=fw)
    dr.rectangle([cx - fw * 0.55, top, cx + fw * 0.55, bottom], fill=255)
    dr.rectangle([left, top + wh * 0.42 - fw * 0.5, right, top + wh * 0.42 + fw * 0.5], fill=255)
    dr.rectangle([left - fw * 1.6, bottom, right + fw * 1.6, bottom + fw * 1.4], fill=255)  # sill
    frame = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255.0
    navy = np.array(NAVY, np.float32) * 0.85
    img[:] = img * (1 - frame) + navy * frame

    # soft bloom of the light past the glass
    g = np.exp(-(((xx - cx) / (ww * 0.75)) ** 2 + ((yy - top - wh * 0.35) / (wh * 0.75)) ** 2))[..., None]
    img[:] = img + (ivory - img) * g * 0.07 * strength


def cover():
    img = navy_sheet(31)
    window(img, W * 0.5, H * 0.50, W * 0.21, H * 0.21)
    return img


def back():
    img = navy_sheet(32)
    window(img, W * 0.5, H * 0.115, W * 0.06, H * 0.06, strength=0.85, floor=False)
    return img


def save_jpg(img, name, q=88):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(ART / name, quality=q, optimize=True,
                                                                 progressive=True, subsampling=0)


def save_page_texture(img, name):
    tex = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    tex.save(ART / f"{name}.jpg", quality=86, optimize=True)
    # one A5 page (148 x 210 mm) holding the texture, for laying under the text pages
    tex.save(ART / f"{name}.pdf", resolution=tex.width / (148 / 25.4))


def main():
    ART.mkdir(exist_ok=True)
    save_page_texture(textured(1240, 1760, PAPER, 7, dark_specks=1 / 1400, light_specks=1 / 3000), "paper")
    save_page_texture(textured(1240, 1760, IVORY, 9, grain=2.2, mottle=1.4, dark_specks=1 / 6000, edge=0.03), "ivory")
    save_jpg(navy_sheet(33), "navy.jpg")
    save_jpg(cover(), "cover.jpg", q=90)
    save_jpg(back(), "back.jpg")
    print("drew paper, ivory, navy, cover, back")


if __name__ == "__main__":
    main()
