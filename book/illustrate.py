#!/usr/bin/env python3
"""Draws the book's illustrations: a white, foggy frozen plain and two small figures.

Every scene is generated from code (no external images), so the art is original and can be
re-drawn at any size. Writes into ./art:
  cover.jpg, back.jpg, khatima.jpg, ch01.jpg ... ch14.jpg   full pages
  end01.png ... end14.png                                    small strips for chapter ends
  strip-title.png, strip-dedication.png                      front matter vignettes
  paper.jpg, paper.pdf                                       page texture for text pages

Usage: python3 illustrate.py
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
ART = ROOT / "art"

PAGE_W, PAGE_H = 1600, 2270          # A5 at ~275 dpi
FOG_TOP = np.array([219, 217, 212], float)
FOG_HOR = np.array([239, 237, 232], float)
SNOW = np.array([242, 240, 235], float)
STREAK = np.array([188, 185, 180], float)
FIGURE = np.array([52, 50, 50], float)

NIGHT_TOP = np.array([16, 20, 30], float)
NIGHT_HOR = np.array([38, 45, 60], float)
NIGHT_SNOW = np.array([30, 36, 48], float)
NIGHT_STREAK = np.array([52, 60, 78], float)
NIGHT_FIGURE = np.array([6, 8, 12], float)


# ---------------------------------------------------------------- noise and ground

def smooth_noise(w, h, cell, rng):
    small = rng.random((max(2, h // cell + 2), max(2, w // cell + 2))).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    img = img.filter(ImageFilter.GaussianBlur(cell / 3))
    a = np.asarray(img, np.float32) / 255.0
    return (a - a.mean()) / (a.std() + 1e-6)


def streak_texture(w, rows, rng):
    """Horizontally stretched noise: drifts of snow blown into long thin lines."""
    out = np.zeros((rows, w), np.float32)
    for cell_x, cell_y, amp in ((420, 5, 1.0), (180, 2, 0.6), (900, 12, 0.5)):
        small = rng.random((rows // cell_y + 3, w // cell_x + 3)).astype(np.float32)
        img = Image.fromarray((small * 255).astype(np.uint8)).resize((w + 2 * cell_x, rows + 2 * cell_y), Image.BICUBIC)
        a = np.asarray(img, np.float32)[cell_y:cell_y + rows, cell_x:cell_x + w] / 255.0
        out += amp * np.clip((a - 0.58) * 3.2, 0, 1)
    return np.clip(out / 1.4, 0, 1)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def plain(w, h, horizon, seed, night=False, streaks=1.0):
    """A foggy sky that melts into a frozen, wind-streaked plain."""
    rng = np.random.default_rng(seed)
    top, hor, snow, streak = ((NIGHT_TOP, NIGHT_HOR, NIGHT_SNOW, NIGHT_STREAK) if night
                              else (FOG_TOP, FOG_HOR, SNOW, STREAK))
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    hy = horizon
    t_sky = np.clip(y / hy, 0, 1) ** 0.9
    sky = top[None, None, :] * (1 - t_sky[..., None]) + hor[None, None, :] * t_sky[..., None]

    # ground: long, thin wind streaks, crowding together toward the horizon
    depth = np.clip((y - hy) / (1 - hy), 1e-3, 1)[:, 0]
    tex_rows = 2400
    tex = streak_texture(w, tex_rows, rng)
    r = np.clip((1.0 / depth - 1.0) * 140, 0, tex_rows - 1).astype(int)
    rows = tex[tex_rows - 1 - r]
    strength = (smoothstep(0.0, 0.7, depth) * 0.75 * streaks)[:, None]
    s = rows * strength
    ground = snow[None, None, :] * (1 - s[..., None]) + streak[None, None, :] * s[..., None]

    # whiteout at the horizon
    blend = smoothstep(hy - 0.012, hy + 0.02, y)
    img = sky * (1 - blend[..., None]) + ground * blend[..., None]
    haze = np.exp(-((y - hy) / 0.05) ** 2)
    img = img * (1 - 0.6 * haze[..., None]) + hor[None, None, :] * (0.6 * haze[..., None])

    # drifting fog and film grain
    fog = smooth_noise(w, h, 380, rng)[..., None]
    img = img + fog * (2.8 if not night else 2.2)
    img = img + rng.normal(0, 2.2, (h, w, 1)).astype(np.float32)
    return img


def fog_mix(color, amount, night=False):
    target = NIGHT_HOR if night else FOG_HOR
    return color * (1 - amount) + target * amount


def paint(img, mask_img, color, opacity=1.0, blur=1.2):
    """Composites an 'L' mask onto the float image in the given color."""
    if blur:
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(blur))
    m = (np.asarray(mask_img, np.float32) / 255.0)[..., None] * opacity
    img *= (1 - m)
    img += np.asarray(color, np.float32)[None, None, :] * m


def new_mask(img):
    return Image.new("L", (img.shape[1], img.shape[0]), 0)


# ---------------------------------------------------------------- figures

def _rot(points, angle, origin):
    ox, oy = origin
    c, s = math.cos(angle), math.sin(angle)
    return [(ox + (x - ox) * c - (y - oy) * s, oy + (x - ox) * s + (y - oy) * c) for x, y in points]


def _limb(d, p1, p2, w, rot):
    x1, y1 = p1
    x2, y2 = p2
    ang = math.atan2(y2 - y1, x2 - x1) + math.pi / 2
    dx, dy = math.cos(ang) * w / 2, math.sin(ang) * w / 2
    poly = [(x1 + dx, y1 + dy), (x2 + dx * 0.85, y2 + dy * 0.85), (x2 - dx * 0.85, y2 - dy * 0.85), (x1 - dx, y1 - dy)]
    d.polygon(rot(poly), fill=255)
    for (x, y), r in (((x1, y1), w / 2), ((x2, y2), w * 0.85 / 2)):
        cx, cy = rot([(x, y)])[0]
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)


def figure(mask, x, y, h, kind="man", pose="stand", face=1, angle=0.0, reach=None, phone=False):
    """Draws a silhouette with its feet at (x, y), `h` pixels tall.

    kind: man | woman.  pose: stand | walk | sit | lie.  face: +1 looks right, -1 left.
    reach: optional (x, y) point the near hand reaches to (for holding hands).
    Returns the point of the chest (for glows).
    """
    d = ImageDraw.Draw(mask)
    origin = (x, y)
    ang = angle + (math.radians(-86) if pose == "lie" else 0)
    rot = lambda pts: _rot(pts, ang, origin)

    def P(u, v):  # body units (fractions of h) to pixels; v measured upward from the feet
        return (x + u * h * face, y - v * h)

    woman = kind == "woman"
    if pose == "sit":
        hip_v, sh_v, head_v = 0.30, 0.64, 0.73
        torso = [P(-0.10, sh_v), P(0.10, sh_v), P(0.09, hip_v), P(-0.11, hip_v)]
        d.polygon(rot(torso), fill=255)
        _limb(d, P(0.0, hip_v), P(0.24, hip_v + 0.01), 0.10 * h, rot)
        _limb(d, P(0.24, hip_v), P(0.25, 0.0), 0.075 * h, rot)
        _limb(d, P(0.06, sh_v - 0.02), P(0.22, hip_v + 0.06), 0.06 * h, rot)
        hx, hy = rot([P(0.02, head_v)])[0]
        r = 0.064 * h
        d.ellipse([hx - r, hy - r * 1.1, hx + r, hy + r * 1.1], fill=255)
        return rot([P(0.05, 0.52)])[0]

    sh = 0.105 if woman else 0.12
    if woman:
        coat = [P(-0.05, 0.875), P(0.05, 0.875), P(0.10, 0.845), P(0.112, 0.78), P(0.095, 0.62),
                P(0.13, 0.33), P(0.10, 0.30), P(-0.10, 0.30), P(-0.13, 0.33), P(-0.095, 0.62),
                P(-0.112, 0.78), P(-0.10, 0.845)]
        leg_top, leg_w, leg_x = 0.32, 0.045, 0.035
    else:
        coat = [P(-0.055, 0.88), P(0.055, 0.88), P(0.11, 0.85), P(0.128, 0.79), P(0.122, 0.62),
                P(0.112, 0.45), P(-0.112, 0.45), P(-0.122, 0.62), P(-0.128, 0.79), P(-0.11, 0.85)]
        leg_top, leg_w, leg_x = 0.47, 0.068, 0.042
    d.polygon(rot(coat), fill=255)
    if pose == "walk":
        _limb(d, P(-0.02, leg_top), P(-0.12, 0.01), leg_w * h, rot)
        _limb(d, P(0.02, leg_top), P(0.10, 0.01), leg_w * h, rot)
    else:
        _limb(d, P(-leg_x, leg_top), P(-leg_x * 0.9, 0.01), leg_w * h, rot)
        _limb(d, P(leg_x, leg_top), P(leg_x * 0.9, 0.01), leg_w * h, rot)
    # arms hang close to the coat
    _limb(d, P(-sh + 0.005, 0.80), P(-sh - 0.012, 0.50), 0.046 * h, rot)
    if reach is not None:
        _limb(d, P(sh - 0.005, 0.80), reach, 0.044 * h, lambda pts: _rot(pts, angle, origin))
    elif phone:
        _limb(d, P(sh - 0.005, 0.80), P(sh + 0.012, 0.63), 0.046 * h, rot)
        _limb(d, P(sh + 0.012, 0.63), P(0.06, 0.67), 0.042 * h, rot)
    else:
        _limb(d, P(sh - 0.005, 0.80), P(sh + 0.012, 0.50), 0.046 * h, rot)
    # neck and head
    _limb(d, P(0.0, 0.86), P(0.004, 0.89), 0.045 * h, rot)
    hx, hy = rot([P(0.01, 0.94)])[0]
    r = (0.05 if woman else 0.054) * h
    d.ellipse([hx - r, hy - r * 1.15, hx + r, hy + r * 1.15], fill=255)
    if woman:  # hair falling to the shoulders
        hair = [P(-0.01, 1.0), P(-0.06, 0.95), P(-0.07, 0.84), P(-0.02, 0.83), P(0.035, 0.9)]
        d.polygon(rot(hair), fill=255)
    return rot([P(0.07, 0.66)])[0]


def contact_shadow(img, x, y, wpx, night=False, strength=0.18):
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    d.ellipse([x - wpx, y - wpx * 0.10, x + wpx, y + wpx * 0.10], fill=255)
    paint(img, m, NIGHT_FIGURE if night else FIGURE, strength, blur=wpx * 0.25)


def person(img, x, y, h, kind, fog=0.0, night=False, **kw):
    """A figure softened by the fog in front of it (fog=0 near, 1 lost)."""
    m = new_mask(img)
    chest = figure(m, x, y, h, kind, **kw)
    col = fog_mix(NIGHT_FIGURE if night else FIGURE, fog, night)
    paint(img, m, col, 1.0, blur=max(1.0, h * 0.016))
    if kw.get("pose") != "lie":
        contact_shadow(img, x, y + 1, h * 0.16, night, 0.16 * (1 - fog))
    return chest


def glow(img, x, y, radius, color, strength):
    h, w = img.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    r2 = ((xx - x) ** 2 + (yy - y) ** 2) / float(radius * radius)
    g = (np.exp(-r2 * 2.2) * strength)[..., None].astype(np.float32)
    img += (np.asarray(color, np.float32)[None, None, :] - img) * g


def crack(img, x0, y0, x1, y1, seed, width=2.0, branches=3, color=None, opacity=0.55, night=False):
    rng = np.random.default_rng(seed)
    m = new_mask(img)
    d = ImageDraw.Draw(m)

    def walk(xa, ya, xb, yb, wdt, depth):
        n = 14
        pts = []
        for i in range(n + 1):
            t = i / n
            jitter = rng.normal(0, 1) * (1 - abs(2 * t - 1)) * 0.06 * math.hypot(xb - xa, yb - ya)
            nx, ny = -(yb - ya), (xb - xa)
            L = math.hypot(nx, ny) or 1
            pts.append((xa + (xb - xa) * t + nx / L * jitter * 0.4, ya + (yb - ya) * t + ny / L * jitter * 0.4))
        d.line(pts, fill=255, width=max(1, int(wdt)), joint="curve")
        if depth > 0:
            for _ in range(branches):
                i = rng.integers(3, n - 2)
                bx, by = pts[i]
                a = math.atan2(yb - ya, xb - xa) + rng.choice([-1, 1]) * rng.uniform(0.4, 1.1)
                L2 = math.hypot(xb - xa, yb - ya) * rng.uniform(0.15, 0.35)
                walk(bx, by, bx + math.cos(a) * L2, by + math.sin(a) * L2 * 0.45, wdt * 0.6, depth - 1)

    walk(x0, y0, x1, y1, width, 2)
    paint(img, m, color if color is not None else (NIGHT_FIGURE if night else FIGURE), opacity, blur=0.9)


def footprints(img, x_near, y_near, x_far, y_far, n, seed, spread=14, opacity=0.35, fade=True):
    rng = np.random.default_rng(seed)
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    for i in range(n):
        t = i / (n - 1)
        tt = t ** 0.55  # steps crowd together with distance
        x = x_near + (x_far - x_near) * tt
        y = y_near + (y_far - y_near) * tt
        size = (1 - tt) * 16 + 2.2
        side = -1 if i % 2 else 1
        xx = x + side * spread * (1 - tt) * 0.9 + rng.normal(0, 1)
        a = int(255 * (1 - tt * 0.75 if fade else 1))
        d.ellipse([xx - size * 0.45, y - size * 0.22, xx + size * 0.45, y + size * 0.22], fill=a)
    paint(img, m, STREAK * 0.75, opacity, blur=1.4)


def save_jpg(img, name, q=88):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(ART / name, quality=q, optimize=True,
                                                                 progressive=True, subsampling=0)


# ---------------------------------------------------------------- scenes

W, H = PAGE_W, PAGE_H
HZ = 0.58  # horizon height as a fraction of the page


def hz(f=HZ):
    return f * H


def scene_cover(seed=1):
    img = plain(W, H, HZ, seed)
    y = hz() + 6
    h = 0.062 * H
    person(img, W * 0.488, y, h * 0.93, "woman", face=1, fog=0.06)
    person(img, W * 0.515, y, h, "man", face=-1, fog=0.04)
    return img


def scene_back(seed=2):
    img = plain(W, H, 0.5, seed)
    footprints(img, W * 0.47, H * 0.98, W * 0.5, hz(0.5) + 8, 26, seed, opacity=0.30)
    footprints(img, W * 0.56, H * 0.98, W * 0.505, hz(0.5) + 8, 26, seed + 1, opacity=0.30)
    return img


def ch01():  # he starts talking to her: a small screen glowing in his hands, she is far away in the fog
    img = plain(W, H, HZ, 101)
    y = hz() + 70
    chest = person(img, W * 0.66, y, 0.085 * H, "man", face=-1, fog=0.0, phone=True)
    glow(img, chest[0] - 4, chest[1], 40, (255, 250, 238), 0.9)
    glow(img, chest[0] - 4, chest[1], 120, (250, 244, 228), 0.25)
    person(img, W * 0.24, hz() + 8, 0.040 * H, "woman", face=1, fog=0.62)
    return img


def ch02():  # talking became a home: close together, hands held, a lit window in the fog behind
    img = plain(W, H, HZ, 102)
    hm = new_mask(img)
    d = ImageDraw.Draw(hm)
    bx, by, bw = W * 0.73, hz() + 2, 120
    d.polygon([(bx, by), (bx + bw, by), (bx + bw, by - 62), (bx + bw / 2, by - 110), (bx, by - 62)], fill=255)
    paint(img, hm, fog_mix(FIGURE, 0.72), 1.0, blur=2.5)
    glow(img, bx + bw * 0.5, by - 38, 26, (255, 236, 196), 0.75)
    win = new_mask(img)
    ImageDraw.Draw(win).rectangle([bx + bw * 0.42, by - 48, bx + bw * 0.58, by - 28], fill=255)
    paint(img, win, (250, 222, 170), 0.85, blur=1.5)
    y = hz() + 40
    h = 0.07 * H
    xm, xw = W * 0.515, W * 0.465
    hand = (W * 0.49, y - 0.47 * h)
    person(img, xw, y, h * 0.93, "woman", face=1, reach=hand)
    person(img, xm, y, h, "man", face=-1, reach=hand)
    return img


def ch03():  # he looks strong and alone; one thin crack runs toward him from where she stands
    img = plain(W, H, HZ, 103)
    y = hz() + 140
    person(img, W * 0.62, y, 0.11 * H, "man", face=-1)
    person(img, W * 0.2, hz() + 10, 0.042 * H, "woman", face=1, fog=0.55)
    crack(img, W * 0.21, hz() + 16, W * 0.6, y + 4, 31, width=1.6, branches=2, opacity=0.4)
    return img


def ch04():  # the accusation: he has fallen, the ice cracks out from where he lies
    img = plain(W, H, HZ, 104)
    y = hz() + 230
    x = W * 0.56
    angles = [-0.5, -0.2, 0.1, 0.35, math.pi - 0.45, math.pi - 0.1, math.pi + 0.2, math.pi + 0.5]
    for i, a in enumerate(angles):
        L = 300 + (i % 3) * 170
        crack(img, x, y, x + math.cos(a) * L, y + math.sin(a) * L * 0.32, 400 + i, width=2.4, branches=2, opacity=0.5)
    person(img, x - 70, y + 14, 0.10 * H, "man", pose="lie", face=1)
    person(img, W * 0.2, hz() + 30, 0.05 * H, "woman", face=1, fog=0.35)
    return img


def ch05():  # waiting for the doctor alone: a bench, and the empty place beside him
    img = plain(W, H, HZ, 105)
    y = hz() + 170
    x0, x1 = W * 0.36, W * 0.70
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    seat = y - 0.03 * H
    d.rectangle([x0, seat - 9, x1, seat + 3], fill=255)
    d.rectangle([x0, seat - 75, x1, seat - 64], fill=255)
    for lx in (x0 + 18, x1 - 30):
        d.rectangle([lx, seat, lx + 10, y], fill=255)
        d.rectangle([lx, seat - 75, lx + 9, seat], fill=255)
    paint(img, m, FIGURE * 1.15, 0.95, blur=1.2)
    contact_shadow(img, (x0 + x1) / 2, y + 2, (x1 - x0) * 0.55, strength=0.12)
    person(img, x1 - 120, y, 0.105 * H, "man", pose="sit", face=-1)
    return img


def ch06():  # the gap nobody made alone: a dark fissure opens in the ice between them
    img = plain(W, H, HZ, 106)
    y = hz() + 60
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    rng = np.random.default_rng(6)
    left, right = [], []
    for i in range(30):
        t = i / 29
        yy = hz() + 4 + (H - hz()) * t ** 1.4
        cx = W * 0.5 + rng.normal(0, 6 + t * 18)
        half = 1 + t ** 1.6 * 70
        left.append((cx - half, yy))
        right.append((cx + half, yy))
    d.polygon(left + right[::-1], fill=255)
    paint(img, m, (150, 160, 172), 0.75, blur=2)
    crack(img, W * 0.5, hz() + 10, W * 0.47, H, 61, width=1.4, branches=4, opacity=0.35)
    person(img, W * 0.23, y, 0.065 * H * 0.93, "woman", face=1, fog=0.1)
    person(img, W * 0.77, y, 0.065 * H, "man", face=-1, fog=0.1)
    return img


def ch07():  # the word he asks for: two figures, and a space between them for the word
    img = plain(W, H, HZ, 107)
    y = hz() + 55
    person(img, W * 0.30, y, 0.063 * H, "woman", face=1, fog=0.12)
    person(img, W * 0.70, y, 0.068 * H, "man", face=-1, fog=0.05)
    return img


def ch08():  # nights when thinking weighs more than the day: a desk, a glowing screen
    img = plain(W, H, 0.6, 108, night=True, streaks=0.6)
    y = hz(0.6) + 160
    xs = W * 0.52
    sx, sy = xs - 40, y - 0.105 * H
    glow(img, sx, sy, 520, (120, 145, 185), 0.35)
    glow(img, sx, sy, 160, (200, 220, 245), 0.45)
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    d.rectangle([xs - 260, y - 0.045 * H - 10, xs + 80, y - 0.045 * H], fill=255)  # desk top
    d.rectangle([xs - 240, y - 0.045 * H, xs - 228, y], fill=255)
    d.rectangle([xs + 56, y - 0.045 * H, xs + 68, y], fill=255)
    d.rectangle([xs - 52, y - 0.045 * H - 30, xs - 30, y - 0.045 * H - 8], fill=255)  # stand
    paint(img, m, NIGHT_FIGURE, 1.0, blur=1.0)
    scr = new_mask(img)
    ImageDraw.Draw(scr).rectangle([sx - 95, sy - 62, sx + 95, sy + 50], fill=255)
    paint(img, scr, (226, 236, 250), 1.0, blur=1.5)
    person(img, xs + 150, y, 0.10 * H, "man", pose="sit", face=-1, night=True)
    return img


def ch09():  # back to the doctor: walking toward a lit door; the horizon beats like a heart
    img = plain(W, H, HZ, 109)
    hy = hz()
    dm = new_mask(img)
    d = ImageDraw.Draw(dm)
    dx = W * 0.3
    d.rectangle([dx - 120, hy - 200, dx + 120, hy + 2], fill=255)
    paint(img, dm, fog_mix(FIGURE, 0.68), 1.0, blur=3)
    door = new_mask(img)
    ImageDraw.Draw(door).rectangle([dx - 26, hy - 90, dx + 26, hy + 2], fill=255)
    paint(img, door, (255, 244, 220), 1.0, blur=1.5)
    glow(img, dx, hy - 40, 90, (255, 246, 226), 0.35)
    ecg = new_mask(img)
    d = ImageDraw.Draw(ecg)
    pts, x = [], 0
    base = hy + 0.002 * H
    beat = [(0, 0), (14, -8), (24, 0), (34, 0), (42, 26), (54, -120), (66, 46), (76, 0), (100, 0), (116, -14), (132, 0)]
    xb0 = W * 0.52
    pts = [(0, base), (xb0, base)] + [(xb0 + bx, base + by) for bx, by in beat] + [(W, base)]
    d.line(pts, fill=255, width=3, joint="curve")
    paint(img, ecg, (160, 82, 94), 0.55, blur=1.0)
    person(img, W * 0.62, hz() + 190, 0.10 * H, "man", pose="walk", face=-1)
    return img


def ch10():  # what I don't want to forget: two sets of footprints, side by side, from the fog
    img = plain(W, H, HZ, 110)
    hy = hz()
    footprints(img, W * 0.40, H * 0.99, W * 0.495, hy + 6, 30, 10, spread=16, opacity=0.42)
    footprints(img, W * 0.58, H * 0.99, W * 0.51, hy + 6, 30, 11, spread=16, opacity=0.42)
    person(img, W * 0.493, hy + 4, 0.030 * H * 0.93, "woman", face=1, fog=0.6)
    person(img, W * 0.512, hy + 4, 0.030 * H, "man", face=-1, fog=0.6)
    return img


def ch11():  # can love make room for our lives: two trodden paths bend toward each other
    img = plain(W, H, HZ, 111)
    hy = hz()
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    for sx, ex in ((W * 0.2, W * 0.47), (W * 0.8, W * 0.53)):
        pts = []
        for i in range(60):
            t = i / 59
            cx = sx + (ex - sx) * (1 - (1 - t) ** 2.2)
            cy = hy + 60 + (H - hy - 60) * t ** 1.6
            pts.append((cx, cy))
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=150, width=int(2 + i * 0.9))
    paint(img, m, STREAK * 0.92, 0.45, blur=4)
    person(img, W * 0.2, hy + 60, 0.048 * H * 0.93, "woman", face=1, fog=0.3)
    person(img, W * 0.8, hy + 60, 0.048 * H, "man", face=-1, fog=0.3)
    return img


def ch12():  # the letter that was not a reproach: a written page resting on the snow
    img = plain(W, H, HZ, 112)
    cx, cy = W * 0.52, H * 0.82
    page = Image.new("L", (520, 700), 0)
    pd = ImageDraw.Draw(page)
    pd.rectangle([0, 0, 519, 699], fill=255)
    lines = Image.new("L", (520, 700), 0)
    ld = ImageDraw.Draw(lines)
    rng = np.random.default_rng(12)
    for i in range(14):
        yy = 80 + i * 40
        x0 = 60 + (rng.integers(0, 120) if i in (0, 13) else 0)
        ld.line([(x0, yy), (470 - (rng.integers(40, 220) if i == 13 else 0), yy)], fill=255, width=4)
    # lay it flat on the ground: squash vertically, rotate a little
    page = page.resize((520, 260)).rotate(-9, expand=True, resample=Image.BICUBIC)
    lines = lines.resize((520, 260)).rotate(-9, expand=True, resample=Image.BICUBIC)
    for layer, col, op in ((page, (252, 251, 248), 1.0), (lines, (120, 124, 132), 0.55)):
        m = new_mask(img)
        m.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
        if layer is page:
            sh = new_mask(img)
            sh.paste(layer, (int(cx - layer.width / 2) + 10, int(cy - layer.height / 2) + 12))
            paint(img, sh, FIGURE, 0.12, blur=10)
        paint(img, m, col, op, blur=1.0)
    person(img, W * 0.28, hz() + 18, 0.045 * H, "woman", face=1, fog=0.45)
    return img


def ch13():  # the man I am trying to be: a long path into the fog, and him on it
    img = plain(W, H, HZ, 113)
    hy = hz()
    m = new_mask(img)
    d = ImageDraw.Draw(m)
    for side in (-1, 1):
        d.line([(W * 0.5 + side * 420, H), (W * 0.5 + side * 6, hy + 2)], fill=255, width=6)
    paint(img, m, STREAK * 0.9, 0.5, blur=3)
    footprints(img, W * 0.5, H * 0.99, W * 0.5, hy + 160, 18, 13, spread=22, opacity=0.35)
    person(img, W * 0.5, hy + 150, 0.075 * H, "man", pose="walk", face=1)
    return img


def ch14():  # still here: he stands clear; she is there, or almost, in the fog behind
    img = plain(W, H, HZ, 114)
    person(img, W * 0.4, hz() + 20, 0.055 * H * 0.93, "woman", face=1, fog=0.7)
    person(img, W * 0.6, hz() + 130, 0.09 * H, "man", face=-1)
    return img


def khatima():  # one line of footprints walking on into the fog
    img = plain(W, H, 0.62, 115)
    footprints(img, W * 0.55, H * 0.995, W * 0.5, hz(0.62) + 6, 28, 15, spread=18, opacity=0.4)
    return img


# ---------------------------------------------------------------- small art

def strip(gap, seed, kind="pair", w=900, h=240):
    """A small fog-and-horizon strip with transparent edges, two tiny figures `gap` apart."""
    img = plain(w, h, 0.62, seed, streaks=0.5)
    y = 0.62 * h + 6
    fh = 0.36 * h
    if kind == "lie":
        person(img, w * 0.55, y + 4, fh, "man", pose="lie", face=1)
        person(img, w * 0.30, y, fh * 0.93, "woman", face=1, fog=0.3)
    elif kind == "alone":
        person(img, w * 0.5, y, fh, "man", face=-1)
    else:
        half = gap * w * 0.42
        person(img, w * 0.5 - half, y, fh * 0.93, "woman", face=1, fog=0.15 if kind != "faint" else 0.62)
        person(img, w * 0.5 + half, y, fh, "man", face=-1)
    xs = np.linspace(-1, 1, w)[None, :]
    ys = np.linspace(-1, 1, h)[:, None]
    alpha = np.clip(np.cos(np.clip(np.abs(xs), 0, 1) * math.pi / 2) ** 1.4, 0, 1) * \
            np.clip(np.cos(np.clip(np.abs(ys * 1.05), 0, 1) * math.pi / 2) ** 0.9, 0, 1)
    rgba = np.dstack([np.clip(img, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def paper(w=1240, h=1760, seed=7, base=(214, 207, 195)):
    """Old book paper: warm grey-beige, speckled, a little darker toward the edges."""
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    img += smooth_noise(w, h, 380, rng)[..., None] * 3.0
    img += smooth_noise(w, h, 40, rng)[..., None] * 1.6
    img += rng.normal(0, 4.2, (h, w, 1)).astype(np.float32)  # fine tooth of the paper
    # speckles: dark flecks and pale fibres pressed into the pulp
    sp = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(sp)
    for _ in range(int(w * h / 900)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([0.5, 0.7, 0.9, 1.2, 1.6], p=[0.4, 0.3, 0.17, 0.09, 0.04])
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(60, 200)))
    f = np.asarray(sp.filter(ImageFilter.GaussianBlur(0.5)), np.float32)[..., None] / 255.0
    img = img * (1 - 0.35 * f) + np.array([120, 110, 98], np.float32) * 0.35 * f
    li = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(li)
    for _ in range(int(w * h / 2500)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(0.6, 1.4)
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(80, 200)))
    f = np.asarray(li.filter(ImageFilter.GaussianBlur(0.6)), np.float32)[..., None] / 255.0
    img = img * (1 - 0.25 * f) + np.array([236, 231, 222], np.float32) * 0.25 * f
    # a softly lit centre, aged edges
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    img *= (1.035 - 0.10 * smoothstep(0.35, 1.45, r))[..., None]
    return img


def on_paper(scene, paper_img, night=False):
    """Prints a scene onto the paper: whites become the paper, greys and figures darken it."""
    ref = NIGHT_SNOW * 4.0 if night else SNOW
    norm = np.clip(scene / ref[None, None, :], 0, 1.08)
    if night:
        norm = np.clip(scene / 255.0, 0, 1) * 1.15
    return paper_img * norm


def ink_layer(rgba):
    """Turns a light-background RGBA strip into a transparent ink layer for the paper:
    the light fog vanishes and only the greys and figures remain."""
    a = np.asarray(rgba, np.float32)
    lum = a[..., :3].mean(axis=2) / SNOW.mean()
    alpha = np.clip(1 - lum, 0, 1) * (a[..., 3] / 255.0)
    alpha = np.clip(alpha * 1.6, 0, 1)
    rgb = np.ones(a.shape[:2] + (3,), np.float32) * np.array([48, 44, 42], np.float32)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- cover

def aged_paper(w, h, seed, base=(214, 208, 197)):
    """Warm, worn paper: mottling, fibres, darker edges."""
    rng = np.random.default_rng(seed)
    img = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    img += smooth_noise(w, h, 420, rng)[..., None] * 4.0
    img += smooth_noise(w, h, 60, rng)[..., None] * 2.2
    img += rng.normal(0, 3.0, (h, w, 1)).astype(np.float32)
    fib = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(fib)
    for _ in range(900):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(8, 40)
        d.line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], fill=int(rng.uniform(40, 120)), width=1)
    f = np.asarray(fib.filter(ImageFilter.GaussianBlur(0.6)), np.float32)[..., None] / 255.0
    img = img * (1 - f * 0.10) + np.array([170, 160, 145], np.float32) * f * 0.10
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    img *= (1 - 0.10 * smoothstep(0.75, 1.45, r))[..., None]
    return img


def wash_mask(w, h, seed, cx=0.5, cy=0.56, rx=0.40, ry=0.33, drips=9):
    """A soft, ragged watercolour shape with drips running up, like ink soaking into paper."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dist = np.sqrt(((xx / w - cx) / rx) ** 2 + ((yy / h - cy) / ry) ** 2)
    field = 1 - dist + smooth_noise(w, h, 220, rng) * 0.16 + smooth_noise(w, h, 50, rng) * 0.06
    a = smoothstep(-0.02, 0.32, field)
    # vertical drips rising from the top of the wash (the fog lifting into the paper)
    drip = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(drip)
    top = (cy - ry * 0.85) * h
    for _ in range(drips):
        x = rng.normal(cx, rx * 0.3) * w
        y0 = top + rng.uniform(20, 90)
        L = rng.uniform(0.04, 0.16) * h
        wd = rng.uniform(3, 7)
        steps = 12
        for k in range(steps):  # tapering toward the tip
            t0, t1 = k / steps, (k + 1) / steps
            d.line([(x, y0 - L * t0), (x, y0 - L * t1)], fill=int(rng.uniform(70, 130) * (1 - t0 * 0.6)),
                   width=max(1, int(wd * (1 - t0 * 0.8))))
    drip = np.asarray(drip.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255.0
    fade = smoothstep(0, 1, (yy - (top - 0.22 * h)) / (0.22 * h))
    a = np.maximum(a, drip * fade * 0.7)
    # a few splashes
    sp = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(sp)
    for _ in range(60):
        ang = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.95, 1.25)
        x = (cx + math.cos(ang) * rx * rr) * w
        y = (cy + math.sin(ang) * ry * rr) * h
        s_ = rng.uniform(1.5, 7)
        d.ellipse([x - s_, y - s_, x + s_, y + s_], fill=int(rng.uniform(80, 200)))
    a = np.maximum(a, np.asarray(sp.filter(ImageFilter.GaussianBlur(1)), np.float32) / 255.0 * 0.6)
    return np.clip(a, 0, 1)


def cover(seed=1):
    """The front cover picture: the two of them in the fog, painted into old paper like a
    watercolour wash (the scene is multiplied into the paper, with pigment pooling at its edges)."""
    paper_img = aged_paper(W, H, 31)
    hzf = 0.60
    scene = plain(W, H, hzf, seed)
    y = hzf * H + 5
    fh = 0.058 * H
    person(scene, W * 0.488, y, fh * 0.93, "woman", face=1, fog=0.03)
    person(scene, W * 0.515, y, fh, "man", face=-1, fog=0.02)
    rng = np.random.default_rng(seed + 9)
    a = wash_mask(W, H, seed + 40, cx=0.5, cy=0.60, rx=0.43, ry=0.27)[..., None]
    norm = np.clip(scene / SNOW[None, None, :], 0, 1.05)
    density = 0.07 + 0.04 * smooth_noise(W, H, 160, rng)[..., None]
    ring = np.clip(a * (1 - a) * 4, 0, 1) ** 1.5 * 0.10
    wash = np.array([0.93, 0.94, 0.96], np.float32)  # a cool grey pigment
    out = paper_img * (1 - a * density - ring) * (1 - a * (1 - norm * wash))
    out = out + 255 * a * 0.09 * (1 - smoothstep(0.0, 0.6, np.abs(np.linspace(-1, 1, H))[:, None, None]))
    return out


def back_cover(seed=2):
    paper_img = aged_paper(W, H, 32)
    rng = np.random.default_rng(seed)
    a = wash_mask(W, H, seed + 50, cx=0.5, cy=0.86, rx=0.46, ry=0.085, drips=0)[..., None]
    scene = plain(W, H, 0.82, seed, streaks=0.8)
    person(scene, W * 0.36, 0.82 * H + 3, 0.026 * H * 0.93, "woman", face=1, fog=0.3)
    person(scene, W * 0.64, 0.82 * H + 3, 0.026 * H, "man", face=-1, fog=0.3)
    norm = np.clip(scene / SNOW[None, None, :], 0, 1.05)
    ring = np.clip(a * (1 - a) * 4, 0, 1) ** 1.5 * 0.12
    out = paper_img * (1 - a * 0.10 - ring) * (1 - a * (1 - norm))
    return out

DISTANCES = {1: 0.62, 2: 0.06, 3: 0.18, 4: 0.5, 5: 0.46, 6: 0.6, 7: 0.52, 8: 0.64, 9: 0.54,
             10: 0.38, 11: 0.32, 12: 0.26, 13: 0.3, 14: 0.22}


def main():
    ART.mkdir(exist_ok=True)
    scenes = {"khatima": khatima,
              "ch01": ch01, "ch02": ch02, "ch03": ch03, "ch04": ch04, "ch05": ch05, "ch06": ch06,
              "ch07": ch07, "ch08": ch08, "ch09": ch09, "ch10": ch10, "ch11": ch11, "ch12": ch12,
              "ch13": ch13, "ch14": ch14}
    save_jpg(cover(), "cover.jpg", q=90)
    save_jpg(back_cover(), "back.jpg", q=88)
    print("drew cover")
    page_paper = paper(W, H, seed=8)
    for name, fn in scenes.items():
        save_jpg(on_paper(fn(), page_paper, night=(name == "ch08")), f"{name}.jpg")
        print("drew", name)
    for n, gap in DISTANCES.items():
        kind = "lie" if n == 4 else ("faint" if n == 14 else "pair")
        ink_layer(strip(gap, 500 + n, kind)).save(ART / f"end{n:02d}.png", optimize=True)
    ink_layer(strip(0.05, 601)).save(ART / "strip-title.png", optimize=True)
    ink_layer(strip(0.12, 602)).save(ART / "strip-dedication.png", optimize=True)
    tex = Image.fromarray(np.clip(paper(), 0, 255).astype(np.uint8))
    tex.save(ART / "paper.jpg", quality=86, optimize=True)
    # one A5 page (148 x 210 mm) holding the texture, for laying under the text pages
    tex.save(ART / "paper.pdf", resolution=tex.width / (148 / 25.4))
    print("drew strips and paper")


if __name__ == "__main__":
    main()
