#!/usr/bin/env python3
"""Draws the trailer's frames-to-be at 1920x1080, in the book's style: fog plates printed on old
paper, and each figure on its own transparent layer so the trailer can move it.

Writes PNG/JPG layers and layout.json (positions the animation needs) into video/build/art.
Usage: python3 video/scenes.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import illustrate as I  # noqa: E402

W, H = 1920, 1080
OUT = HERE / "build" / "art"
I.W, I.H = W, H  # the book's scene functions read these
HZ = 0.58
layout = {}


def hz(f=HZ):
    return f * H


PAPER = None


def printed(scene, night=False):
    return I.on_paper(scene, PAPER, night=night)


def save_plate(img, name):
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / f"{name}.jpg", quality=90, subsampling=0)


def sprite(name, x, y, h, kind, fog=0.0, night=False, **kw):
    """One figure alone on a transparent full frame, with its soft contact shadow."""
    m = Image.new("L", (W, H), 0)
    chest = I.figure(m, x, y, h, kind, **kw)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(max(1.0, h * 0.016))), np.float32) / 255.0
    if kw.get("pose") != "lie":
        sh = Image.new("L", (W, H), 0)
        r = h * 0.16
        ImageDraw.Draw(sh).ellipse([x - r, y + 1 - r * 0.1, x + r, y + 1 + r * 0.1], fill=255)
        s = np.asarray(sh.filter(ImageFilter.GaussianBlur(r * 0.25)), np.float32) / 255.0 * 0.16 * (1 - fog)
        a = np.maximum(a, s)
    col = I.fog_mix(I.NIGHT_FIGURE if night else I.FIGURE, fog, night) * 0.9
    rgba = np.dstack([np.ones((H, W, 3), np.float32) * col, a * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT / f"{name}.png", optimize=True)
    layout[name] = {"x": x, "y": y, "h": h, "chest": list(chest)}
    return chest


def main():
    global PAPER
    OUT.mkdir(parents=True, exist_ok=True)
    PAPER = I.paper(W, H, seed=8)

    # 1–2: the first plain, shared by the opening and the two drawing closer
    save_plate(printed(I.plain(W, H, HZ, 101)), "plain1")
    sprite("man_phone", W * 0.64, hz() + 46, 0.12 * H, "man", face=-1, phone=True)
    sprite("man1", W * 0.64, hz() + 46, 0.12 * H, "man", face=-1)
    sprite("woman1", W * 0.47, hz() + 46, 0.12 * H * 0.93, "woman", face=1)
    layout["woman_far"] = {"x": W * 0.22, "y": hz() + 8, "scale": 0.42}

    # 3: home, a lit window in the fog behind them
    img = I.plain(W, H, HZ, 102)
    hm = I.new_mask(img)
    bx, by, bw = W * 0.70, hz() + 2, 110
    ImageDraw.Draw(hm).polygon([(bx, by), (bx + bw, by), (bx + bw, by - 58), (bx + bw / 2, by - 100), (bx, by - 58)], fill=255)
    I.paint(img, hm, I.fog_mix(I.FIGURE, 0.72), 1.0, blur=2.5)
    win = I.new_mask(img)
    ImageDraw.Draw(win).rectangle([bx + bw * 0.42, by - 44, bx + bw * 0.58, by - 26], fill=255)
    I.paint(img, win, (250, 222, 170), 0.85, blur=1.5)
    save_plate(printed(img), "home")
    layout["window"] = {"x": bx + bw * 0.5, "y": by - 35}
    y = hz() + 40
    hgt = 0.11 * H
    hand = (W * 0.49, y - 0.47 * hgt)
    m = Image.new("L", (W, H), 0)
    I.figure(m, W * 0.462, y, hgt * 0.93, "woman", face=1, reach=hand)
    I.figure(m, W * 0.518, y, hgt, "man", face=-1, reach=hand)
    a = np.asarray(m.filter(ImageFilter.GaussianBlur(1.8)), np.float32) / 255.0
    rgba = np.dstack([np.ones((H, W, 3), np.float32) * I.FIGURE * 0.9, a * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT / "couple.png", optimize=True)

    # 4: the fall; cracks on their own layer so they can spread from where he falls
    save_plate(printed(I.plain(W, H, HZ, 104)), "ice")
    fx, fy = W * 0.56, hz() + 190
    sprite("man_stand", fx, fy, 0.14 * H, "man", face=-1)
    sprite("man_fallen", fx - 60, fy + 12, 0.13 * H, "man", pose="lie", face=1)
    sprite("woman_ice", W * 0.2, hz() + 26, 0.06 * H, "woman", face=1, fog=0.35)
    cr = np.full((H, W, 3), 255.0, np.float32)
    angles = [-0.5, -0.2, 0.1, 0.35, math.pi - 0.45, math.pi - 0.1, math.pi + 0.2, math.pi + 0.5]
    for i, ang in enumerate(angles):
        L = 330 + (i % 3) * 190
        I.crack(cr, fx, fy, fx + math.cos(ang) * L, fy + math.sin(ang) * L * 0.32, 400 + i, width=2.6, branches=2, opacity=0.9)
    alpha = np.clip(1 - cr.mean(axis=2) / 255.0, 0, 1) * 0.6
    rgba = np.dstack([np.ones((H, W, 3), np.float32) * np.array([52, 50, 50]), alpha * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT / "cracks.png", optimize=True)
    layout["impact"] = {"x": fx, "y": fy}

    # 5: the gap; 6: the night of questions; 7: the two of them apart
    save_plate(printed(I.ch06()), "gap")
    save_plate(printed(I.ch08(), night=True), "night")
    xs, ynight = W * 0.52, I.hz(0.6) + 160
    layout["screen"] = {"x": xs - 40, "y": ynight - 0.105 * H}
    save_plate(printed(I.ch07()), "apart")

    # 8: still here; she is there, or almost
    save_plate(printed(I.plain(W, H, HZ, 114)), "plain2")
    sprite("man_end", W * 0.6, hz() + 120, 0.15 * H, "man", face=-1)
    sprite("woman_end", W * 0.4, hz() + 22, 0.075 * H * 0.93, "woman", face=1, fog=0.55)

    # 9: the title: the two of them in a watercolour wash on old paper
    paper_img = I.aged_paper(W, H, 31)
    hzf = 0.66
    scene = I.plain(W, H, hzf, 1)
    yy = hzf * H + 4
    fh = 0.075 * H
    I.person(scene, W * 0.488, yy, fh * 0.93, "woman", face=1, fog=0.03)
    I.person(scene, W * 0.515, yy, fh, "man", face=-1, fog=0.02)
    a = I.wash_mask(W, H, 41, cx=0.5, cy=0.68, rx=0.30, ry=0.26, drips=7)[..., None]
    norm = np.clip(scene / I.SNOW[None, None, :], 0, 1.05)
    rng = np.random.default_rng(10)
    density = 0.07 + 0.04 * I.smooth_noise(W, H, 160, rng)[..., None]
    ring = np.clip(a * (1 - a) * 4, 0, 1) ** 1.5 * 0.10
    out = paper_img * (1 - a * density - ring) * (1 - a * (1 - norm * np.array([0.93, 0.94, 0.96], np.float32)))
    save_plate(out, "title")

    # drifting fog and film grain, laid over everything
    rng = np.random.default_rng(5)
    fw = int(W * 1.6)
    f = np.clip(I.smooth_noise(fw, H, 320, rng) * 0.5 + 0.2, 0, 1)
    f *= np.clip(np.linspace(0.4, 1.2, H)[:, None], 0, 1)
    fog = np.dstack([np.full((H, fw, 3), [244, 242, 237], np.float32), f * 0.33 * 255]).astype(np.uint8)
    Image.fromarray(fog, "RGBA").save(OUT / "fog.png", optimize=True)
    for k in range(4):
        g = rng.normal(0, 1, (H // 2, W // 2))
        gr = np.dstack([np.full((H // 2, W // 2, 3), 128, np.float32) + g[..., None] * 60,
                        np.full((H // 2, W // 2), 255 * 0.07)]).clip(0, 255).astype(np.uint8)
        Image.fromarray(gr, "RGBA").save(OUT / f"grain{k}.png", optimize=True)

    (OUT / "layout.json").write_text(json.dumps(layout, indent=1))
    print("drew trailer art into", OUT)


if __name__ == "__main__":
    main()
