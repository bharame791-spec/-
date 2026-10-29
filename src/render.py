"""RAM logo: layer-by-layer trim-path reveal + "قريباً", with synthesized sound design.

The logo is split into its real layers straight from the artwork (by colour and
connectivity).  Each layer is drawn on along its own path: the reveal follows the
geodesic distance inside the layer from its tip, so the front always cuts across
the ribbon like an After Effects Trim Path on a stroked shape.

Usage:
    python3 src/render.py            -> out/coming_soon.mp4
    python3 src/render.py --preview  -> out/preview_###.png every 0.5s
"""
import heapq
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "out")

W, H, FPS = 1080, 1920, 30
DUR = 8.0
SR = 48000
N = int(DUR * FPS)
SCALE = H / 1536          # artwork 1024x1536 -> cover 1920 tall
CROP_X = (round(1024 * SCALE) - W) // 2

# Timeline (seconds): (start, end) of each layer's trim path
T_LAYERS = [(0.35, 1.35),   # top ribbon
            (1.00, 2.55),   # second ribbon -> ring -> arrow head -> outer crescent
            (2.20, 2.85)]   # grey inner crescent
T_HIT = 2.9                 # logo complete: shine + accent
T_BAR = 3.15                # divider bar grows, names slide out of it
T_SUB = 3.75                # subtitle
T_SOON0, T_SOON1 = 4.55, 5.55   # "قريباً"
T_GLINT = 6.05
T_OUT = 7.45

rng = np.random.default_rng(7)
PREVIEW = None  # set of frame indices -> PNGs instead of video


def clamp01(x):
    return np.clip(x, 0, 1)


def ease_out(x):
    return 1 - (1 - clamp01(x)) ** 3


def ease_io(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def blur(a, r):
    if r < 0.3:
        return a
    if a.ndim == 3:
        return np.stack([nd.gaussian_filter(a[..., c], r) for c in range(a.shape[2])], -1)
    return nd.gaussian_filter(a, r)


# ---------------------------------------------------------------- artwork
def load_art():
    src = Image.open(os.path.join(ASSETS, "logo_clean.png")).convert("RGB")
    src = src.resize((round(src.width * SCALE), H), Image.LANCZOS)
    return np.asarray(src, np.float32)[:, CROP_X:CROP_X + W] / 255


def segment(art):
    r, g, b = art[..., 0] * 255, art[..., 1] * 255, art[..., 2] * 255
    lum = (r + g + b) / 3
    blue = (b - r > 40) & (lum < 200)
    grey = (np.abs(b - r) < 60) & (lum < 190) & (lum > 100) & ~blue
    yy = np.arange(H)[:, None]
    logo_zone = yy < 920 * SCALE
    lab, n = nd.label(blue & logo_zone)
    sizes = nd.sum(np.ones_like(lab), lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1]
    comps = [lab == order[k] + 1 for k in range(2)]
    comps.sort(key=lambda m: np.nonzero(m)[0].min())  # top ribbon first
    glab, gn = nd.label(grey & logo_zone)
    gs = nd.sum(np.ones_like(glab), glab, range(1, gn + 1))
    comps.append(glab == np.argmax(gs) + 1)

    text = (blue | grey) & (yy >= 920 * SCALE) & (yy < 1080 * SCALE)
    title = text & (yy < 1015 * SCALE)
    subtitle = text & (yy >= 1015 * SCALE)
    return comps, title, subtitle


def geodesic(mask, seed):
    """Dijkstra distance inside mask from seed (y, x), normalised to [0, 1]."""
    ys, xs = np.nonzero(mask)
    y0, x0, y1, x1 = ys.min(), xs.min(), ys.max() + 1, xs.max() + 1
    m = mask[y0:y1, x0:x1]
    h, w = m.shape
    dist = np.full((h, w), np.inf)
    sy, sx = seed[0] - y0, seed[1] - x0
    dist[sy, sx] = 0
    pq = [(0.0, sy, sx)]
    nb = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
          (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    while pq:
        d, y, x = heapq.heappop(pq)
        if d > dist[y, x]:
            continue
        for dy, dx, c in nb:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and m[yy, xx]:
                nd_ = d + c
                if nd_ < dist[yy, xx]:
                    dist[yy, xx] = nd_
                    heapq.heappush(pq, (nd_, yy, xx))
    finite = np.isfinite(dist)
    dist[~finite] = 0
    dist /= dist.max()
    full = np.full(mask.shape, 2.0, np.float32)
    full[y0:y1, x0:x1][finite] = dist[finite]
    return full


def clean_plate(art, ink):
    """Background with every logo/text pixel removed (normalised-convolution inpaint)."""
    hole = nd.binary_dilation(ink, iterations=10)
    keep = (~hole).astype(np.float32)
    out = art.copy()
    todo = hole.copy()
    for r in (8, 20, 45, 90):
        fill = blur(art * keep[..., None], r) / (nd.gaussian_filter(keep, r)[..., None] + 1e-6)
        ok = todo & (nd.gaussian_filter(keep, r) > 0.05)
        out[ok] = fill[ok]
        todo &= ~ok
    soft = nd.gaussian_filter(hole.astype(np.float32), 2)[..., None]
    return blur(out, 6) * soft + art * (1 - soft)


def render_text(word, size):
    ar = ImageFont.truetype(os.path.join(ASSETS, "cairo-arabic-800-normal.woff"), size)
    qf = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.62))
    img = Image.new("L", (W, size * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((W // 2, size), word, font=ar, fill=255, anchor="mm", direction="rtl", language="ar")
    l, t, r, b = d.textbbox((W // 2, size), word, font=ar, anchor="mm", direction="rtl", language="ar")
    d.text((r + size * 0.03, t + size * 0.02), '"', font=qf, fill=255, anchor="lt")
    d.text((l - size * 0.03, t + size * 0.02), '"', font=qf, fill=255, anchor="rt")
    return np.asarray(img, np.float32) / 255


def over(frame, color, alpha):
    a = alpha[..., None]
    return frame * (1 - a) + color * a


# ---------------------------------------------------------------- frames
def render_video(path_noaudio):
    art = load_art()
    comps, title, subtitle = segment(art)
    plate = clean_plate(art, comps[0] | comps[1] | comps[2] | title | subtitle)

    # per-layer reveal fields; masks are dilated so anti-aliased edges come along
    layers = []
    taken = np.zeros((H, W), bool)
    for m in comps:
        md = nd.binary_dilation(m, iterations=3) & ~taken
        taken |= md
        ys, xs = np.nonzero(m)
        k = np.argmin(ys)
        layers.append((md, geodesic(md, (ys[k], xs[k]))))
    logo_mask = taken
    ys, xs = np.nonzero(logo_mask)
    cx, cy = xs.mean(), ys.mean()
    navy = np.median(art[comps[1]], 0)

    # title split at the divider bar
    tys, txs = np.nonzero(title)
    cols = np.nonzero(title.sum(0))[0]
    groups = np.split(cols, np.nonzero(np.diff(cols) > 3)[0] + 1)
    mid = (txs.min() + txs.max()) / 2
    bar = min(groups, key=lambda g: abs(g.mean() - mid) + 1000 * (len(g) > 25))
    bar_x0, bar_x1 = bar.min() - 2, bar.max() + 3
    bar_y0, bar_y1 = tys.min(), tys.max()
    title_d = nd.binary_dilation(title, iterations=2).astype(np.float32)
    sub_d = nd.binary_dilation(subtitle, iterations=2).astype(np.float32)
    _, sxs = np.nonzero(subtitle)
    sub_x0, sub_x1 = sxs.min(), sxs.max()

    soon = render_text("قريباً", 112)
    s_h = soon.shape[0]
    soon_y = int(1165 * SCALE) - s_h // 2
    scols = np.nonzero(soon.max(0) > 0.05)[0]
    sx0, sx1 = scols.min(), scols.max()

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    colsx = np.arange(W, dtype=np.float32)
    rows = np.arange(H, dtype=np.float32)

    proc = None
    if PREVIEW is None:
        proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
             "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", path_noaudio],
            stdin=subprocess.PIPE)

    for i in range(N):
        t = i / FPS
        frame = plate.copy()

        # ---- logo layers: trim path along each layer, one after another
        reveal = np.zeros((H, W), np.float32)
        head = np.zeros((H, W), np.float32)
        for (md, dist), (t0, t1) in zip(layers, T_LAYERS):
            p = ease_io((t - t0) / (t1 - t0))
            if p <= 0:
                continue
            p *= 1.02
            reveal += clamp01((p - dist) / 0.012) * md
            if p < 1.02:
                head += np.exp(-((dist - p) / 0.025) ** 2) * md * (dist <= p + 0.005)
        reveal = nd.gaussian_filter(clamp01(reveal), 0.7)
        # soft contact shadow gives the layers depth while they draw
        sh = np.roll(nd.gaussian_filter(reveal, 8), 8, 0) * (1 - reveal)
        frame *= 1 - (sh * 0.12)[..., None]
        frame = over(frame, art, reveal)

        # light streak riding each trim head
        if head.any():
            hl = nd.gaussian_filter(head, 1.5)
            frame += (hl * 0.6 * reveal)[..., None] * (1 - frame)
            frame += blur(hl, 12)[..., None] * 0.30 * np.array([0.5, 0.65, 1.0]) * (1 - frame)

        # shine sweep across the finished logo
        gp = (t - T_HIT) / 0.75
        if 0 < gp < 1:
            band = (xx - cx) * 0.55 + (yy - cy) * 0.85
            pos = -420 + gp * 900
            sw = np.exp(-((band - pos) / 28) ** 2) * logo_mask
            frame += (nd.gaussian_filter(sw, 1.5) * 0.45)[..., None] * (1 - frame)

        # ---- title: the divider grows, then the names slide out from behind it
        bp = ease_out((t - T_BAR) / 0.35)
        if bp > 0:
            ymid = (bar_y0 + bar_y1) / 2
            half = (bar_y1 - bar_y0) / 2 * bp
            band_y = clamp01(half + 1 - np.abs(rows - ymid))[:, None]
            bm = np.zeros((H, W), np.float32)
            bm[:, bar_x0:bar_x1] = 1
            frame = over(frame, art, bm * band_y * title_d)
        npg = ease_out((t - T_BAR - 0.2) / 0.75)
        if npg > 0:
            shift = int(round((1 - npg) * 150))
            fade_in = clamp01(npg * 1.8)
            for side, sgn in ((xx >= bar_x1, -1), (xx < bar_x0, 1)):
                m = np.roll(title_d * side, sgn * shift, 1) * side * fade_in
                frame = over(frame, np.roll(art, sgn * shift, 1), m)

        # ---- subtitle: right-to-left soft wipe
        sp = (t - T_SUB) / 0.8
        if sp > 0:
            edge = sub_x1 + 20 - (sub_x1 - sub_x0 + 120) * ease_io(sp)
            frame = over(frame, art, clamp01((colsx - edge) / 50)[None, :] * sub_d)

        # ---- "قريباً": RTL reveal, blur -> sharp, rise, then glint
        tp = (t - T_SOON0) / (T_SOON1 - T_SOON0)
        if tp > 0:
            e = ease_out(tp)
            edge = sx1 + 10 - (sx1 - sx0 + 90) * ease_io(tp * 1.1)
            wipe = clamp01((colsx - edge) / 45)[None, :]
            y0 = soon_y + int((1 - e) * 30)
            tl = np.zeros((H, W), np.float32)
            tl[y0:y0 + s_h] = blur(soon, (1 - e) * 8) * wipe * clamp01(tp * 2.5)
            frame *= 1 - (np.roll(nd.gaussian_filter(tl, 6), 6, 0) * 0.12)[..., None]
            frame = over(frame, navy, tl)
            gp2 = (t - T_GLINT) / 0.6
            if 0 < gp2 < 1:
                pos = sx0 - 60 + (sx1 - sx0 + 120) * gp2
                sw = np.exp(-((colsx - pos) / 26) ** 2)[None, :] * tl
                frame += (sw * 0.6)[..., None] * (1 - frame)

        # ---- camera: gentle push-in with a small settle bump at the hit
        z = 1.06 - 0.06 * ease_out(t / 3.2) + 0.010 * clamp01((t - 3.2) / 4.8)
        z += 0.012 * np.exp(-max(t - T_HIT, 0) * 6) * (t >= T_HIT)
        fade = ease_io(t / 0.3) * (1 - ease_io((t - T_OUT) / (DUR - T_OUT)))
        frame = np.clip(frame, 0, 1) * fade + (1 - fade)  # fade from / to white

        img = Image.fromarray((frame * 255).astype(np.uint8))
        img = img.transform((W, H), Image.AFFINE,
                            (1 / z, 0, cx - cx / z, 0, 1 / z, cy - cy / z),
                            resample=Image.BICUBIC, fillcolor=(235, 236, 240))
        arr = np.asarray(img, np.int16) + rng.integers(-1, 2, (H, W, 1))
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        if proc is None:
            if i in PREVIEW:
                Image.fromarray(arr).save(os.path.join(OUT, f"preview_{i:03d}.png"))
            continue
        proc.stdin.write(arr.tobytes())
        if i % 15 == 0:
            print(f"frame {i}/{N}", file=sys.stderr, flush=True)
    if proc:
        proc.stdin.close()
        proc.wait()


# ---------------------------------------------------------------- audio
def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) / d)


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp_sweep(noise, f0, f1, q=2.0, block=512):
    """Band-passed noise with a moving centre frequency (whoosh)."""
    out = np.zeros_like(noise)
    nb = len(noise) // block + 1
    zi = None
    for k in range(nb):
        seg = noise[k * block:(k + 1) * block]
        if not len(seg):
            break
        fc = f0 * (f1 / f0) ** (k / max(nb - 1, 1))
        lo, hi = max(fc - fc / q / 2, 20), min(fc + fc / q / 2, SR / 2 - 100)
        b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
        if zi is None:
            zi = np.zeros(max(len(a), len(b)) - 1)
        out[k * block:(k + 1) * block], zi = signal.lfilter(b, a, seg, zi=zi)
    return out


def place(buf, x, t0, pan=0.0, gain=1.0):
    """Add mono x at t0; pan is a scalar or a per-sample array in [-1, 1]."""
    i0 = int(t0 * SR)
    if i0 >= len(buf):
        return
    x = x[:len(buf) - i0]
    pan = np.broadcast_to(pan, x.shape) if np.ndim(pan) else pan
    if np.ndim(pan):
        pan = pan[:len(x)]
    buf[i0:i0 + len(x), 0] += x * gain * np.cos((pan + 1) * np.pi / 4) * 1.414
    buf[i0:i0 + len(x), 1] += x * gain * np.sin((pan + 1) * np.pi / 4) * 1.414


def secs(d):
    return np.arange(int(d * SR)) / SR


def whoosh(d, f0, f1, q=1.6, shape=1.5):
    t = secs(d)
    return bp_sweep(rng.normal(0, 1, len(t)), f0, f1, q=q) * np.sin(np.pi * t / d) ** shape


def ping(f, dur=0.25, amp=1.0):
    t = secs(dur)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t)
    return x * env(len(t), 0.002, dur / 5) * amp


def bell(freqs, dur, decay=1.0):
    t = secs(dur)
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / (decay * d)) * a
            for f, d, a in freqs)
    return x * np.minimum(t / 0.003, 1)


def make_reverb(seconds=2.6):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.stack([lp(rng.normal(0, 1, n), 7500), lp(rng.normal(0, 1, n), 7500)], 1)
    ir *= np.exp(-t / 0.5)[:, None]
    ir[: int(0.015 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))


def render_audio(path):
    n = int((DUR + 0.3) * SR)
    dry = np.zeros((n, 2))
    send = np.zeros((n, 2))

    # bed: soft airy pad swelling in, low drone rising into the logo hit
    t = secs(T_HIT)
    f = 49 * 2 ** (t / T_HIT)
    drone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    place(dry, drone * (t / T_HIT) ** 2 * 0.16, 0)
    riser = bp_sweep(rng.normal(0, 1, len(t)), 250, 5000, q=3) * (t / T_HIT) ** 3
    place(dry, riser, 0, pan=-0.25, gain=0.25)
    place(send, riser, 0, pan=0.25, gain=0.3)

    # one whoosh per trim-path layer, panned along the stroke's travel
    for (t0, t1), (f0, f1), pans in zip(
            T_LAYERS, [(3200, 700), (2600, 450), (4200, 1500)],
            [(-0.2, 0.6), (0.5, -0.6), (0.4, -0.3)]):
        d = t1 - t0 + 0.15
        w = whoosh(d, f0, f1)
        pan = np.linspace(*pans, len(w))
        place(dry, w, t0 - 0.05, pan=pan, gain=0.42)
        place(send, w, t0 - 0.05, pan=-pan, gain=0.22)
        # tiny "lock" tick when each layer lands
        tk = hp(rng.normal(0, 1, int(0.03 * SR)), 2500) * env(int(0.03 * SR), 0.0005, 0.006)
        place(dry, tk, t1, pan=pans[1], gain=0.25)
        place(send, tk, t1, gain=0.3)
        for s in np.sort(rng.uniform(t0, t1, 14)):
            p = ping(rng.uniform(4500, 9500), amp=rng.uniform(0.012, 0.03))
            place(send, p, s, pan=rng.uniform(-0.8, 0.8))

    # logo hit: reverse swell, sub boom, punch, bell shimmer
    t = secs(0.55)
    place(dry, bp_sweep(rng.normal(0, 1, len(t)), 700, 4000, q=1.2) * (t / 0.55) ** 4,
          T_HIT - 0.55, gain=0.35)
    t = secs(2.4)
    fsub = 42 + 100 * np.exp(-t / 0.045)
    sub = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env(len(t), 0.002, 0.6)
    place(dry, np.tanh(sub * 2.0) * 0.7, T_HIT)
    crack = hp(rng.normal(0, 1, int(0.3 * SR)), 1200) * env(int(0.3 * SR), 0.001, 0.045)
    place(dry, crack, T_HIT, gain=0.22)
    place(send, crack, T_HIT, gain=0.5)
    shim = bell([(523.25, 1.4, .30), (784, 1.1, .22), (1046.5, 0.9, .18),
                 (1567.98, 0.7, .12), (2093, 0.5, .08), (2637, 0.4, .05)], 3.0)
    place(dry, shim, T_HIT, pan=-0.1, gain=0.2)
    place(send, shim, T_HIT, pan=0.1, gain=0.4)
    g = whoosh(0.75, 5000, 11000, q=4, shape=3)            # shine sweep "shing"
    place(dry, g, T_HIT, pan=np.linspace(-0.5, 0.5, len(g)), gain=0.16)
    place(send, g, T_HIT, gain=0.2)

    # divider: soft mechanical tick + stereo split swish as the names slide out
    tk = lp(hp(rng.normal(0, 1, int(0.05 * SR)), 1500), 6000) * env(int(0.05 * SR), 0.0005, 0.01)
    place(dry, tk, T_BAR, gain=0.35)
    place(send, tk, T_BAR, gain=0.35)
    sw = whoosh(0.7, 5500, 1800, q=2, shape=2)
    place(dry, sw, T_BAR + 0.15, pan=np.linspace(0, -0.8, len(sw)), gain=0.2)
    place(dry, whoosh(0.7, 5200, 1700, q=2, shape=2), T_BAR + 0.15,
          pan=np.linspace(0, 0.8, len(sw)), gain=0.2)
    place(send, sw, T_BAR + 0.15, gain=0.15)
    sw = whoosh(0.8, 7000, 3000, q=2.5, shape=2)           # subtitle wipe
    place(dry, sw, T_SUB, pan=np.linspace(0.6, -0.6, len(sw)), gain=0.12)

    # "قريباً": airy swish, warm pad, right-to-left chime arpeggio
    d = T_SOON1 - T_SOON0 + 0.3
    sw = whoosh(d, 6000, 1400, q=2, shape=2)
    place(dry, sw, T_SOON0, pan=np.linspace(0.6, -0.6, len(sw)), gain=0.22)
    place(send, sw, T_SOON0, gain=0.25)
    t = secs(3.2)
    pad = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.4)
              for f in [130.81, 196.0, 261.63, 329.63, 392.0])
    pad = lp(pad * np.minimum(t / 0.7, 1) * np.exp(-np.maximum(t - 1.3, 0) / 1.0), 2500)
    place(dry, pad, T_SOON0, gain=0.03)
    place(send, pad, T_SOON0, gain=0.045)
    for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        c = ping(f, dur=1.6, amp=0.10)
        place(dry, c, T_SOON0 + 0.1 + k * 0.17, pan=0.6 - k * 0.4)
        place(send, c, T_SOON0 + 0.1 + k * 0.17, gain=1.2)
    g = whoosh(0.6, 4500, 11000, q=4, shape=3)             # glint on the word
    place(dry, g, T_GLINT, pan=np.linspace(-0.4, 0.4, len(g)), gain=0.16)
    place(send, g, T_GLINT, gain=0.22)
    for s in np.sort(rng.uniform(T_GLINT, T_GLINT + 0.6, 8)):
        place(send, ping(rng.uniform(6000, 10000), amp=0.03), s, pan=rng.uniform(-1, 1))

    ir = make_reverb()
    wet = np.stack([signal.fftconvolve(send[:, c], ir[:, c])[:n] for c in range(2)], 1)
    mix = dry + wet * 0.9
    mix = np.stack([hp(mix[:, c], 28) for c in range(2)], 1)
    mix /= np.abs(mix).max()
    mix = np.tanh(mix * 1.6) / np.tanh(1.6)
    fade_n = int(0.6 * SR)
    mix[-fade_n:] *= np.linspace(1, 0, fade_n)[:, None]
    pcm = (mix * 0.89 * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def main():
    global PREVIEW
    os.makedirs(OUT, exist_ok=True)
    if "--preview" in sys.argv:
        PREVIEW = set(range(0, N, 15))
        render_video(None)
        return
    wav = os.path.join(OUT, "sfx.wav")
    vid = os.path.join(OUT, "_video.mp4")
    render_audio(wav)
    render_video(vid)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav,
                    "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart",
                    os.path.join(OUT, "coming_soon.mp4")], check=True)
    os.remove(vid)


if __name__ == "__main__":
    main()
