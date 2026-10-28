"""Trace the supplied RAM mark into clean vector layers (navy base, light-blue bands, grey crescent)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
import potrace

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
OUT = os.path.join(HERE, "out9")
os.makedirs(OUT, exist_ok=True)

X0, Y0, X1, Y1 = 340, 355, 720, 905          # crop around the mark in the source image
K = 6                                          # upsampling factor before tracing

im = Image.open(SRC).convert("RGB").crop((X0, Y0, X1, Y1))
big = im.resize((im.width*K, im.height*K), Image.LANCZOS)
a = np.asarray(big).astype(np.int16)
r, g, b = a[..., 0], a[..., 1], a[..., 2]
L = 0.30*r + 0.59*g + 0.11*b


def clean(mask, open_px=0, blur=4):
    m = Image.fromarray((mask*255).astype(np.uint8))
    if open_px:
        m = m.filter(ImageFilter.MinFilter(open_px)).filter(ImageFilter.MaxFilter(open_px))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(m) > 127


blue = clean((b - r > 45) & (b > 70), 0, 7)
light = clean(blue & (L > 60) & (b - r > 45), 21, 11)
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
box = (xx > (450-X0)*K) & (xx < (600-X0)*K) & (yy > (720-Y0)*K) & (yy < (895-Y0)*K)
grey = clean(box & (np.abs(b - r) < 42) & (L > 115) & (L < 190), 9, 4)


def trace(mask):
    bm = potrace.Bitmap(~mask)
    plist = bm.trace(turdsize=60, turnpolicy=potrace.POTRACE_TURNPOLICY_MINORITY,
                     alphamax=1.15, opticurve=True, opttolerance=0.5)
    parts = []
    for curve in plist:
        sx, sy = curve.start_point.x/K, curve.start_point.y/K
        d = [f"M{sx:.2f} {sy:.2f}"]
        for s in curve.segments:
            if s.is_corner:
                d.append(f"L{s.c.x/K:.2f} {s.c.y/K:.2f} L{s.end_point.x/K:.2f} {s.end_point.y/K:.2f}")
            else:
                d.append(f"C{s.c1.x/K:.2f} {s.c1.y/K:.2f} {s.c2.x/K:.2f} {s.c2.y/K:.2f} {s.end_point.x/K:.2f} {s.end_point.y/K:.2f}")
        parts.append(" ".join(d) + " Z")
    return " ".join(parts)


paths = {"blue": trace(blue), "light": trace(light), "grey": trace(grey),
         "size": [X1 - X0, Y1 - Y0]}
json.dump(paths, open(os.path.join(OUT, "paths.json"), "w"))
for k in ("blue", "light", "grey"):
    Image.fromarray(((blue if k == "blue" else light if k == "light" else grey)*255).astype(np.uint8)).resize(
        (X1 - X0, Y1 - Y0)).save(os.path.join(OUT, f"mask-{k}.png"))
print({k: len(v) for k, v in paths.items() if k != "size"})
