#!/usr/bin/env python3
"""Draws the illustrations for «ما زلت خائفًا، ما زلت وحيدًا» in the style of the first book
(fog, small silhouettes, old paper) but colder: ash-grey paper, falling dust, and one small warm
light (a window, a phone) as the only hope in the pictures.

Reuses the drawing primitives of ../book/illustrate.py. Writes into ./art.
Usage: python3 illustrate.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent


def _load_first_book():
    """The first book's illustrate.py, loaded under its own name (this file shares its filename)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("book1_illustrate", HERE.parent / "book" / "illustrate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


I = _load_first_book()

ART = HERE / "art"
W, H = I.PAGE_W, I.PAGE_H
I.W, I.H = W, H

ASH = (203, 199, 192)          # the paper: old, and grey like ash
AMBER = np.array([226, 178, 112], np.float32)
WARM = np.array([246, 226, 190], np.float32)
METAL = np.array([74, 76, 80], np.float32)
FIG = I.FIGURE
PAPER = None


def printed(scene, night=False):
    return I.on_paper(scene, PAPER, night=night)


def mask_of(img):
    return I.new_mask(img)


def fill(img, draw_fn, color, opacity=1.0, blur=1.2):
    """Draws shapes into a mask (filled unless told otherwise) and paints the mask in `color`."""
    m = mask_of(img)
    d = ImageDraw.Draw(m)
    d.ink = d.draw.draw_ink(255)
    d.fill = True  # shapes drawn without an explicit fill are filled with white
    draw_fn(d)
    I.paint(img, m, color, opacity, blur=blur)


# ---------------------------------------------------------------- places and things

def interior(seed, floor=0.66):
    """A bare wall meeting a floor: the fog plain with almost no streaks, a little darker above."""
    img = I.plain(W, H, floor, seed, streaks=0.22)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    img *= 1 - 0.10 * (1 - y)
    return img


def dust(img, seed, n=420, top=0.0, bottom=1.0, light=False, size=1.0):
    """Specks of dust or ash drifting down; a few are close and soft, most are far and small."""
    rng = np.random.default_rng(seed)
    m = mask_of(img)
    d = ImageDraw.Draw(m)
    for _ in range(n):
        x = rng.uniform(0, W)
        y = rng.uniform(top, bottom) ** 1.0 * H
        r = rng.choice([0.8, 1.1, 1.5, 2.2, 3.4], p=[0.4, 0.3, 0.17, 0.09, 0.04]) * size
        streak = r * rng.uniform(1.0, 2.6)  # a little motion as they fall
        d.ellipse([x - r, y - streak, x + r, y + streak], fill=int(rng.uniform(70, 220)))
    col = WARM if light else FIG * 1.6
    I.paint(img, m, col, 0.55 if light else 0.35, blur=1.1)


def window_light(img, cx, top, ww, wh, floor_y, beam_dx=0.0, strength=1.0, seed=0, bars=True):
    """A small high window letting in warm light; its beam falls to the floor through the dust."""
    left, right, bottom = cx - ww / 2, cx + ww / 2, top + wh
    # the beam: from the glass down to a patch on the floor, fading
    beam = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(beam)
    spread = ww * 1.25
    fx = cx + beam_dx
    d.polygon([(left, top + wh * 0.1), (right, top + wh * 0.1), (fx + spread, floor_y), (fx - spread, floor_y)], fill=255)
    b = np.asarray(beam.filter(ImageFilter.GaussianBlur(ww * 0.22)), np.float32) / 255.0
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    fade = np.clip(1 - (yy * H - top) / (floor_y - top + 1), 0.25, 1.0)
    a = (b * fade * 0.48 * strength)[..., None]
    img[:] = img * (1 - a) + WARM * a
    # the patch of light on the floor
    patch = Image.new("L", (W, H), 0)
    ImageDraw.Draw(patch).ellipse([fx - spread * 1.1, floor_y - ww * 0.18, fx + spread * 1.1, floor_y + ww * 0.32], fill=255)
    p = (np.asarray(patch.filter(ImageFilter.GaussianBlur(ww * 0.2)), np.float32) / 255.0 * 0.42 * strength)[..., None]
    img[:] = img * (1 - p) + WARM * p
    # dust shines only inside the beam
    rng = np.random.default_rng(seed)
    m = mask_of(img)
    dd = ImageDraw.Draw(m)
    for _ in range(int(260 * strength)):
        t = rng.uniform(0.05, 1.0)
        y = top + (floor_y - top) * t
        half = (ww / 2) + (spread - ww / 2) * t
        x = cx + beam_dx * t + rng.uniform(-half, half) * 0.85
        r = rng.choice([0.9, 1.3, 1.8, 2.6])
        dd.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(120, 255)))
    I.paint(img, m, np.array([252, 240, 216], np.float32), 0.8 * strength, blur=0.8)
    # the glass and its frame
    fill(img, lambda dr: dr.rectangle([left, top, right, bottom]), WARM * 0.98 + 2, 0.92 * strength, blur=1.5)
    I.glow(img, cx, top + wh / 2, ww * 1.3, (252, 236, 204), 0.5 * strength)
    if bars:
        fw = max(3, ww * 0.03)
        def frame(dr):
            dr.rectangle([left, top, right, bottom], outline=255, width=int(fw))
            dr.rectangle([cx - fw / 2, top, cx + fw / 2, bottom], fill=255)
            dr.rectangle([left, top + wh * 0.45 - fw / 2, right, top + wh * 0.45 + fw / 2], fill=255)
        fill(img, frame, FIG * 1.5, 0.85, blur=1.0)


def bench(img, x0, x1, floor_y, seat_h, back=True):
    """A long metal bench seen from the front: seat, two back rails, thin legs."""
    seat = floor_y - seat_h
    def draw(d):
        d.rectangle([x0, seat - seat_h * 0.06, x1, seat + seat_h * 0.03], fill=255)
        if back:
            for k in (0.55, 0.85):
                yb = seat - seat_h * k
                d.rectangle([x0 + 4, yb - seat_h * 0.035, x1 - 4, yb + seat_h * 0.035], fill=255)
        for lx in np.linspace(x0 + seat_h * 0.12, x1 - seat_h * 0.12, 4):
            d.rectangle([lx - seat_h * 0.03, seat, lx + seat_h * 0.03, floor_y], fill=255)
            if back:
                d.rectangle([lx - seat_h * 0.025, seat - seat_h * 0.9, lx + seat_h * 0.025, seat], fill=255)
    fill(img, draw, METAL, 0.95, blur=1.2)
    # a cold glint along the seat
    fill(img, lambda d: d.rectangle([x0, seat - seat_h * 0.06, x1, seat - seat_h * 0.045]), (170, 172, 176), 0.5, blur=1.0)
    I.contact_shadow(img, (x0 + x1) / 2, floor_y + 2, (x1 - x0) * 0.55, strength=0.10)
    return seat


def hunched(mask, x, seat_y, h, face=-1):
    """Someone sitting bent forward, elbows on knees, head bowed over a phone. Returns the phone."""
    d = ImageDraw.Draw(mask)
    def P(u, v):
        return (x + u * h * face, seat_y - v * h)
    ident = lambda pts: pts
    torso = [P(-0.09, 0.0), P(0.08, 0.01), P(0.17, 0.25), P(0.11, 0.33), P(0.0, 0.33), P(-0.06, 0.26)]
    d.polygon(torso, fill=255)
    I._limb(d, P(0.0, 0.02), P(0.22, 0.05), 0.11 * h, ident)        # thigh
    I._limb(d, P(0.22, 0.05), P(0.24, -0.27), 0.075 * h, ident)     # shin to the floor
    I._limb(d, P(0.10, 0.30), P(0.20, 0.09), 0.055 * h, ident)      # upper arm to the knee
    I._limb(d, P(0.20, 0.09), P(0.17, 0.17), 0.05 * h, ident)       # forearm up to the hands
    hx, hy = P(0.165, 0.375)
    r = 0.056 * h
    d.ellipse([hx - r, hy - r * 1.1, hx + r, hy + r * 1.1], fill=255)
    return P(0.17, 0.18)


def person(img, x, y, h, kind="man", fog=0.0, night=False, alpha=1.0, **kw):
    m = mask_of(img)
    chest = I.figure(m, x, y, h, kind, **kw)
    col = I.fog_mix(I.NIGHT_FIGURE if night else FIG, fog, night)
    I.paint(img, m, col, alpha, blur=max(1.0, h * 0.016))
    if kw.get("pose") not in ("lie", "sit"):
        I.contact_shadow(img, x, y + 1, h * 0.16, night, 0.16 * (1 - fog) * alpha)
    return chest, m


def boy_on_bench(img, x, seat_y, h, face=-1, glow_strength=1.0):
    m = mask_of(img)
    phone = hunched(m, x, seat_y, h, face)
    I.paint(img, m, FIG, 1.0, blur=max(1.0, h * 0.016))
    I.glow(img, phone[0], phone[1], h * 0.09, tuple(AMBER + 20), 0.75 * glow_strength)
    I.glow(img, phone[0], phone[1], h * 0.25, tuple(AMBER), 0.22 * glow_strength)
    fill(img, lambda d: d.rectangle([phone[0] - h * 0.012, phone[1] - h * 0.016, phone[0] + h * 0.012, phone[1] + h * 0.016]),
         np.array([255, 236, 200], np.float32), 0.9 * glow_strength, blur=0.8)
    return phone


def house(img, x, y, w, h, lit=(), fog=0.55, split=0.0):
    """A house in the fog; `lit` lists window positions (fractions) glowing warm; `split` opens a gap."""
    def body(d):
        roof = h * 0.38
        if split:
            g = w * split / 2
            d.polygon([(x - w / 2, y), (x - g, y), (x - g, y - h + roof * 0.35), (x - w / 2, y - h + roof)], fill=255)
            d.polygon([(x + g, y), (x + w / 2, y), (x + w / 2, y - h + roof), (x + g, y - h + roof * 0.25)], fill=255)
        else:
            d.polygon([(x - w / 2, y), (x + w / 2, y), (x + w / 2, y - h + roof), (x, y - h), (x - w / 2, y - h + roof)], fill=255)
    fill(img, body, I.fog_mix(FIG, fog), 1.0, blur=2.0)
    for fx, fy in lit:
        wx, wy = x - w / 2 + fx * w, y - fy * h
        s = w * 0.045
        I.glow(img, wx, wy, s * 3.2, (240, 205, 150), 0.18)
        fill(img, lambda d: d.rectangle([wx - s, wy - s * 1.3, wx + s, wy + s * 1.3]), np.array([250, 222, 168], np.float32), 1.0, blur=1.0)


def tent(img, x, y, w, h, fog=0.25):
    def draw(d):
        d.polygon([(x - w / 2, y), (x, y - h), (x + w / 2, y)], fill=255)
    fill(img, draw, I.fog_mix(FIG, fog), 1.0, blur=1.6)
    fill(img, lambda d: d.polygon([(x - w * 0.06, y), (x, y - h * 0.5), (x + w * 0.06, y)]), I.fog_mix(FIG, fog) * 0.6, 0.9, blur=1)


def chair(img, x, floor_y, s, face=1, fog=0.15):
    def draw(d):
        seat = floor_y - s * 0.45
        d.rectangle([x - s * 0.22, seat - s * 0.04, x + s * 0.22, seat + s * 0.02], fill=255)
        bx = x - s * 0.22 * face
        d.rectangle([bx - s * 0.025, seat - s * 0.5, bx + s * 0.025, floor_y], fill=255)
        d.rectangle([x + s * 0.2 * face - s * 0.022, seat, x + s * 0.2 * face + s * 0.022, floor_y], fill=255)
    fill(img, draw, I.fog_mix(FIG, fog), 1.0, blur=1.2)


def ghost_outline(img, m, opacity=0.35):
    """Only the outline of a figure: someone who should be here and is not."""
    edge = m.filter(ImageFilter.MaxFilter(5))
    e = np.asarray(edge, np.float32) - np.asarray(m, np.float32)
    rng = np.random.default_rng(3)
    dash = (np.sin(np.arange(W)[None, :] * 0.25 + np.arange(H)[:, None] * 0.25) > -0.2)
    e = np.clip(e, 0, 255) * dash
    I.paint(img, Image.fromarray(e.astype(np.uint8)), FIG, opacity, blur=0.6)


# ---------------------------------------------------------------- chapter scenes

def ch01():  # before I knew what loss meant: the family together in a house with every window lit
    img = I.plain(W, H, 0.6, 201)
    img *= 0.86                      # dusk
    house(img, W * 0.5, H * 0.6 + 4, W * 0.34, H * 0.16, lit=[(0.2, 0.28), (0.4, 0.28), (0.6, 0.28), (0.8, 0.28), (0.5, 0.56)], fog=0.08)
    dust(img, 1, 120, 0.0, 0.5, size=0.8)
    return img


def ch02():  # the metal bench: the boy bent over his phone; a stranger sits beside him
    img = interior(202)
    floor = H * 0.66 + 120
    seat = bench(img, W * 0.18, W * 0.86, floor, H * 0.05)
    boy_on_bench(img, W * 0.62, seat, H * 0.15, face=1)
    person(img, W * 0.40, floor, H * 0.15 * 0.98, "man", pose="sit", face=1)
    dust(img, 2, 160, 0.0, 0.6, size=0.8)
    return img


def ch03():  # the crossing: he and his mother are through; behind the line, only fog where his father should be
    img = I.plain(W, H, 0.58, 203)
    hz = H * 0.58
    for i, px in enumerate(np.linspace(W * 0.05, W * 0.95, 13)):
        fill(img, lambda d, px=px: d.rectangle([px - 7, hz - 70, px + 7, hz + 40]), I.fog_mix(FIG, 0.35), 1.0, blur=1.5)
    fill(img, lambda d: d.rectangle([0, hz - 62, W, hz - 54]), I.fog_mix(FIG, 0.4), 1.0, blur=1.5)
    fill(img, lambda d: d.rectangle([0, hz - 12, W, hz - 5]), I.fog_mix(FIG, 0.4), 1.0, blur=1.5)
    person(img, W * 0.40, hz + 260, H * 0.13 * 0.93, "woman", face=-1)
    person(img, W * 0.58, hz + 290, H * 0.14, "man", face=1)
    m = Image.new("L", (W, H), 0)
    I.figure(m, W * 0.5, hz + 30, H * 0.08, "man", face=1)
    ghost_outline(img, m, 0.6)
    return img


def ch04():  # bread became a responsibility: tents by the sea, a sack of flour on his shoulder
    img = I.plain(W, H, 0.52, 204, streaks=0.5)
    hz = H * 0.52
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    sea = ((y * H > hz) & (y * H < hz + H * 0.07)).astype(np.float32)
    sea = np.asarray(Image.fromarray((sea[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)[..., None] / 255
    img[:] = img * (1 - sea * 0.28) + np.array([150, 158, 166], np.float32) * sea * 0.28
    for tx, tw, f in [(0.18, 0.16, 0.45), (0.33, 0.12, 0.5), (0.74, 0.18, 0.3), (0.9, 0.1, 0.5)]:
        tent(img, W * tx, hz + H * 0.105, W * tw, W * tw * 0.62, fog=f)
    fill(img, lambda d: d.polygon([(W * 0.6, hz + H * 0.11), (W * 0.66, hz + H * 0.09), (W * 0.67, hz + H * 0.11), (W * 0.61, hz + H * 0.125)]),
         np.array([60, 66, 80], np.float32), 0.9, blur=1)
    _, m = person(img, W * 0.47, hz + H * 0.26, H * 0.15, "man", pose="walk", face=1)
    fh = H * 0.15
    sx, sy = W * 0.47 + fh * 0.07, hz + H * 0.26 - fh * 0.9
    fill(img, lambda d: d.ellipse([sx - fh * 0.17, sy - fh * 0.10, sx + fh * 0.13, sy + fh * 0.05]), FIG, 1.0, blur=fh * 0.016)
    return img


def ch05():  # the ones I left in yesterday: walking away from a lit house in the night fog
    img = I.plain(W, H, 0.6, 205, night=True, streaks=0.6)
    hz = H * 0.6
    house(img, W * 0.3, hz + 10, W * 0.24, H * 0.11, lit=[(0.5, 0.35)], fog=0.0)
    I.footprints(img, W * 0.33, hz + 30, W * 0.62, hz + 330, 14, 5, spread=10, opacity=0.25, fade=False)
    person(img, W * 0.66, hz + 360, H * 0.13, "man", pose="walk", face=1, night=True)
    return img


def ch06():  # fourteen days, and the house that broke in two
    img = I.plain(W, H, 0.6, 206)
    hz = H * 0.6
    house(img, W * 0.5, hz + 8, W * 0.46, H * 0.24, fog=0.3, split=0.10)
    dust(img, 6, 520, 0.25, 0.62, size=1.1)
    for k in range(14):  # fourteen days counted on the ground
        x = W * 0.25 + k * W * 0.036
        fill(img, lambda d, x=x: d.line([(x, hz + 300), (x + 6, hz + 360)], fill=255, width=6), FIG, 0.55, blur=1)
    fill(img, lambda d: d.line([(W * 0.24, hz + 350), (W * 0.76, hz + 310)], fill=255, width=5), FIG, 0.45, blur=1)
    return img


def ch07():  # the result that was not complete: he holds the paper up to a row of empty chairs
    img = interior(207, 0.62)
    floor = H * 0.62 + 300
    for i, cx in enumerate(np.linspace(W * 0.16, W * 0.84, 6)):
        chair(img, cx, floor + 120, H * 0.10, face=1 if cx < W / 2 else -1, fog=0.15)
    _, _ = person(img, W * 0.5, floor - 120, H * 0.13, "man", face=1)
    px, py = W * 0.5 + H * 0.13 * 0.05, floor - 120 - H * 0.13 * 0.72
    fill(img, lambda d: d.rectangle([px, py - 40, px + 46, py + 18]), np.array([246, 242, 232], np.float32), 1.0, blur=1)
    I.glow(img, px + 23, py - 10, 120, (248, 236, 210), 0.3)
    return img


def ch08():  # the brother my mother did not bear: two friends on a low wall at night; one is no longer there
    img = I.plain(W, H, 0.6, 208, night=True, streaks=0.5)
    hz = H * 0.6
    wall_top = hz + 200
    fill(img, lambda d: d.rectangle([W * 0.12, wall_top, W * 0.88, wall_top + 90]), I.NIGHT_FIGURE * 2.2, 1.0, blur=1.5)
    person(img, W * 0.42, wall_top + 140, H * 0.14, "man", pose="sit", face=1, night=True)
    person(img, W * 0.60, wall_top + 140, H * 0.14, "man", pose="sit", face=-1, night=True, alpha=0.28)
    dust(img, 8, 200, 0.0, 0.6, light=True, size=0.7)
    return img


def ch09():  # what doesn't show in the picture: he stands upright; his shadow sits curled on the ground
    img = I.plain(W, H, 0.58, 209)
    hz = H * 0.58
    x, y, h = W * 0.36, hz + 300, H * 0.16
    person(img, x, y, h, "man", face=1)
    up = Image.new("L", (W, H), 0)
    hunched(up, x - h * 0.24, y - h * 0.27, h, face=1)  # its feet where his feet are
    # flip it about the feet and lay it along the ground, stretching away to the side
    k, m = 0.9, 0.6
    sh = up.transform((W, H), Image.AFFINE, (1, -k / m, k * y / m, 0, -1 / m, y + y / m), resample=Image.BICUBIC)
    I.paint(img, sh, FIG * 1.7, 0.45, blur=5)
    return img


def ch10():  # the ledger: an open notebook of columns on the floor
    img = interior(210, 0.6)
    cx, cy = W * 0.52, H * 0.8
    pg = Image.new("L", (900, 620), 0)
    pd = ImageDraw.Draw(pg)
    pd.rectangle([0, 0, 440, 619], fill=255)
    pd.rectangle([460, 0, 899, 619], fill=255)
    lines = Image.new("L", (900, 620), 0)
    ld = ImageDraw.Draw(lines)
    for col in (0, 460):
        for i in range(14):
            yy = 60 + i * 38
            ld.line([(col + 40, yy), (col + 400, yy)], fill=150, width=3)
        ld.line([(col + 300, 40), (col + 300, 590)], fill=200, width=4)
        rng = np.random.default_rng(col)
        for i in range(12):
            if rng.random() < 0.7:
                yy = 52 + i * 38
                ld.line([(col + 320, yy), (col + 380, yy - 6)], fill=255, width=5)
    pg = pg.resize((900, 300)).rotate(-6, expand=True, resample=Image.BICUBIC)
    lines = lines.resize((900, 300)).rotate(-6, expand=True, resample=Image.BICUBIC)
    for layer, col, op in ((pg, (248, 245, 238), 1.0), (lines, (90, 92, 98), 0.6)):
        m = mask_of(img)
        m.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
        if layer is pg:
            sm = mask_of(img)
            sm.paste(layer, (int(cx - layer.width / 2) + 14, int(cy - layer.height / 2) + 16))
            I.paint(img, sm, FIG, 0.15, blur=12)
        I.paint(img, m, col, op, blur=1.0)
    dust(img, 10, 120, 0.0, 0.7, size=0.7)
    return img


def ch11():  # what nobody knew I had planned: a doorway standing alone, a house never built around it
    img = I.plain(W, H, 0.58, 211)
    hz = H * 0.58
    x, y = W * 0.55, hz + 160
    dw, dh = W * 0.14, H * 0.2
    def frame(d):
        t = 14
        d.rectangle([x - dw / 2, y - dh, x - dw / 2 + t, y], fill=255)
        d.rectangle([x + dw / 2 - t, y - dh, x + dw / 2, y], fill=255)
        d.rectangle([x - dw / 2, y - dh, x + dw / 2, y - dh + t], fill=255)
    fill(img, frame, I.fog_mix(FIG, 0.15), 1.0, blur=1.4)
    rng = np.random.default_rng(11)
    for _ in range(9):
        bx, by = x + rng.uniform(-dw * 1.6, dw * 1.6), y + rng.uniform(5, 60)
        s = rng.uniform(16, 30)
        fill(img, lambda d, bx=bx, by=by, s=s: d.rectangle([bx, by - s * 0.6, bx + s, by]), I.fog_mix(FIG, 0.3), 0.9, blur=1)
    person(img, W * 0.22, hz + 40, H * 0.06, "man", face=1, fog=0.45)
    return img


def ch12():  # the question before tomorrow: the family in a row, and outlines where some of them stood
    img = I.plain(W, H, 0.58, 212)
    hz = H * 0.58
    y = hz + 160
    xs = np.linspace(W * 0.12, W * 0.88, 9)
    missing = {1, 3, 4, 7}
    for i, x in enumerate(xs):
        kind = "woman" if i % 3 == 1 else "man"
        h = H * (0.10 if i not in (2, 6) else 0.07)
        if i in missing:
            m = Image.new("L", (W, H), 0)
            I.figure(m, x, y, h, kind, face=1)
            ghost_outline(img, m, 0.4)
        else:
            person(img, x, y, h, kind, face=1)
    return img


def ch13():  # still here: alone in the fog, the dust still falling
    img = I.plain(W, H, 0.58, 213)
    person(img, W * 0.56, H * 0.58 + 160, H * 0.14, "man", face=-1)
    dust(img, 13, 600, 0.0, 0.9, size=1.0)
    return img


def ch14():  # the last chapter: a small window opened in the wall of the years; he stands at the edge of its light
    img = interior(214, 0.66)
    floor = H * 0.66 + 200
    window_light(img, W * 0.5, H * 0.30, W * 0.16, H * 0.13, floor, beam_dx=-W * 0.02, strength=1.2, seed=14)
    person(img, W * 0.66, floor + 40, H * 0.15, "man", face=-1)
    return img


# ---------------------------------------------------------------- cover and small art

def cover():
    """The two halves of the title on old ash paper, over a wash of the hospital night: a small high
    window, its beam falling through the dust onto the empty part of a long metal bench, and the boy
    at the far end of it, bent over the light of his phone."""
    paper_img = I.aged_paper(W, H, 51, base=(201, 197, 190))
    scene = interior(301, 0.70)
    floor = H * 0.70 + 150
    window_light(scene, W * 0.38, H * 0.43, W * 0.11, H * 0.10, floor - H * 0.05, beam_dx=W * 0.03, strength=1.7, seed=31)
    seat = bench(scene, W * 0.18, W * 0.84, floor, H * 0.045)
    boy_on_bench(scene, W * 0.74, seat, H * 0.15, face=1, glow_strength=1.3)
    dust(scene, 32, 260, 0.38, 0.95, size=0.8)
    a = I.wash_mask(W, H, 61, cx=0.5, cy=0.68, rx=0.44, ry=0.27, drips=8)[..., None]
    norm = np.clip(scene / I.SNOW[None, None, :], 0, 1.35)  # let the window's light shine past the paper
    rng = np.random.default_rng(7)
    density = 0.08 + 0.04 * I.smooth_noise(W, H, 160, rng)[..., None]
    ring = np.clip(a * (1 - a) * 4, 0, 1) ** 1.5 * 0.11
    out = paper_img * (1 - a * density - ring) * (1 - a * (1 - norm))
    # ash falling over the whole cover, even outside the picture
    dust(out, 33, 160, 0.0, 1.0, size=0.9)
    return out


def back_cover():
    paper_img = I.aged_paper(W, H, 52, base=(201, 197, 190))
    scene = interior(302, 0.80)
    floor = H * 0.80 + 120
    seat = bench(scene, W * 0.28, W * 0.72, floor, H * 0.03)
    a = I.wash_mask(W, H, 62, cx=0.5, cy=0.86, rx=0.34, ry=0.085, drips=0)[..., None]
    norm = np.clip(scene / I.SNOW[None, None, :], 0, 1.1)
    ring = np.clip(a * (1 - a) * 4, 0, 1) ** 1.5 * 0.1
    out = paper_img * (1 - a * 0.1 - ring) * (1 - a * (1 - norm))
    dust(out, 34, 120, 0.0, 1.0, size=0.8)
    return out


def end_mark(seed, empty=False, w=900, h=240):
    """A small strip for chapter ends: the bench, and the boy on it (or the bench left empty)."""
    img = I.plain(w, h, 0.7, seed, streaks=0.2)
    floor = h * 0.86
    sv_w, sv_h = I.W, I.H
    I.W, I.H = w, h
    global W, H
    W0, H0 = W, H
    W, H = w, h
    try:
        seat = bench(img, w * 0.25, w * 0.75, floor, h * 0.16)
        if not empty:
            boy_on_bench(img, w * 0.66, seat, h * 0.42, face=1, glow_strength=0.8)
    finally:
        I.W, I.H = sv_w, sv_h
        W, H = W0, H0
    xs = np.linspace(-1, 1, w)[None, :]
    ys = np.linspace(-1, 1, h)[:, None]
    alpha = np.clip(np.cos(np.clip(np.abs(xs), 0, 1) * math.pi / 2) ** 1.2, 0, 1) * \
            np.clip(np.cos(np.clip(np.abs(ys * 1.05), 0, 1) * math.pi / 2) ** 0.8, 0, 1)
    rgba = np.dstack([np.clip(img, 0, 255), alpha * 255]).astype(np.uint8)
    return I.ink_layer(Image.fromarray(rgba, "RGBA"))


def charcoal_brush():
    """The first book's brush stroke, in charcoal instead of rose."""
    b = Image.open(HERE.parent / "book" / "art" / "brush.png").convert("RGBA")
    a = np.asarray(b, np.float32)
    rgb = np.ones(a.shape[:2] + (3,), np.float32) * np.array([58, 55, 52], np.float32)
    rgb += I.smooth_noise(a.shape[1], a.shape[0], 120, np.random.default_rng(2))[..., None] * 4
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8), "RGBA")


def main():
    global PAPER
    ART.mkdir(exist_ok=True)
    PAPER = I.paper(W, H, seed=21, base=ASH)
    I.save_jpg.__globals__["ART"] = ART  # write into this book's art folder
    I.save_jpg(cover(), "cover.jpg", q=90)
    I.save_jpg(back_cover(), "back.jpg", q=88)
    print("drew cover")
    scenes = [ch01, ch02, ch03, ch04, ch05, ch06, ch07, ch08, ch09, ch10, ch11, ch12, ch13, ch14]
    night = {5, 8}
    for n, fn in enumerate(scenes, 1):
        I.save_jpg(printed(fn(), night=n in night), f"ch{n:02d}.jpg")
        print("drew chapter", n)
    end_mark(401).save(ART / "end.png", optimize=True)
    end_mark(402, empty=True).save(ART / "end-empty.png", optimize=True)
    charcoal_brush().save(ART / "brush.png", optimize=True)
    tex = Image.fromarray(np.clip(I.paper(seed=22, base=ASH), 0, 255).astype(np.uint8))
    tex.save(ART / "paper.jpg", quality=86, optimize=True)
    tex.save(ART / "paper.pdf", resolution=tex.width / (148 / 25.4))
    print("drew strips, brush and paper")


if __name__ == "__main__":
    main()
