"""Logo reveal + "قريباً" coming-soon animation (1080x1920, 30fps) with synthesized sound design.

Usage: python3 src/render.py            -> out/coming_soon.mp4
"""
import heapq
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as nd
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ROOT, "out")

W, H, FPS = 1080, 1920, 30
DUR = 7.5
SR = 48000
N = int(DUR * FPS)

# Timeline (seconds)
T_DRAW0, T_DRAW1 = 0.35, 2.55   # pen draws the logo
T_HIT = 2.6                     # flash / impact
T_TEXT0, T_TEXT1 = 3.05, 4.25   # "قريباً" reveal
T_GLINT = 4.7                   # light sweep
T_OUT = 6.7                     # fade out start

rng = np.random.default_rng(7)
PREVIEW = None  # set of frame indices -> PNGs instead of video


def ease_out(x):
    x = np.clip(x, 0, 1)
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def smooth_band(x, lo, hi):
    return ease_io((x - lo) / max(hi - lo, 1e-6))


# ---------------------------------------------------------------- logo plate
def load_plate():
    src = Image.open(os.path.join(ASSETS, "logo.png")).convert("RGB")
    s = W / src.width
    src = src.resize((W, round(src.height * s)), Image.LANCZOS)
    plate = np.zeros((H, W, 3), np.float32)
    oy = (H - src.height) // 2 - 60
    plate[oy:oy + src.height] = np.asarray(src, np.float32) / 255
    return plate, s, oy


def logo_mask(plate, s, oy):
    L = plate.mean(2) * 255
    hp = L - nd.gaussian_filter(L, 25 * s)
    e = nd.gaussian_filter(np.abs(hp), 4 * s)
    m = e > 4
    m[int(oy + 1080 * s):] = False  # keep the mark only, not the caption below it
    m = nd.binary_closing(m, iterations=6)
    m = nd.binary_fill_holes(m)
    lab, n = nd.label(m)
    m = lab == (np.argmax(nd.sum(m, lab, range(1, n + 1))) + 1)
    return m, hp


def geodesic(mask, seed, step=3):
    """Dijkstra distance inside mask from seed, on a coarse grid, upsampled back."""
    sm = mask[::step, ::step]
    h, w = sm.shape
    dist = np.full((h, w), np.inf)
    sy, sx = seed[0] // step, seed[1] // step
    ys, xs = np.nonzero(sm)
    k = np.argmin((ys - sy) ** 2 + (xs - sx) ** 2)
    sy, sx = ys[k], xs[k]
    dist[sy, sx] = 0
    pq = [(0.0, sy, sx)]
    nb = [(-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1),
          (-1, -1, 1.414), (-1, 1, 1.414), (1, -1, 1.414), (1, 1, 1.414)]
    while pq:
        d, y, x = heapq.heappop(pq)
        if d > dist[y, x]:
            continue
        for dy, dx, c in nb:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and sm[yy, xx]:
                nd_ = d + c
                if nd_ < dist[yy, xx]:
                    dist[yy, xx] = nd_
                    heapq.heappush(pq, (nd_, yy, xx))
    fill = np.where(np.isinf(dist), np.nanmax(dist[np.isfinite(dist)]), dist)
    full = np.kron(fill, np.ones((step, step)))[:mask.shape[0], :mask.shape[1]]
    full = nd.gaussian_filter(full, 2)
    return full / full[mask].max()


# ---------------------------------------------------------------- text
def render_text(word, size):
    """Arabic word in Cairo, wrapped in quotes (Cairo has no curly-quote glyphs)."""
    ar = ImageFont.truetype(os.path.join(ASSETS, "cairo-arabic-800-normal.woff"), size)
    qf = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.7))
    img = Image.new("L", (W, size * 2), 0)
    d = ImageDraw.Draw(img)
    d.text((W // 2, size), word, font=ar, fill=255, anchor="mm", direction="rtl", language="ar")
    l, t, r, b = d.textbbox((W // 2, size), word, font=ar, anchor="mm", direction="rtl", language="ar")
    gap = size * 0.02
    d.text((r + gap, t - size * 0.05), '"', font=qf, fill=255, anchor="lt")
    d.text((l - gap, t - size * 0.05), '"', font=qf, fill=255, anchor="rt")
    return np.asarray(img, np.float32) / 255


def blur(a, r):
    if r < 0.3:
        return a
    if a.ndim == 3:
        return np.stack([nd.gaussian_filter(a[..., c], r) for c in range(a.shape[2])], -1)
    return nd.gaussian_filter(a, r)


def fast_bloom(img, r):
    """Cheap wide blur via downscale."""
    f = 4
    small = img[::f, ::f]
    b = blur(small, r / f)
    return np.repeat(np.repeat(b, f, 0), f, 1)[:img.shape[0], :img.shape[1]]


# ---------------------------------------------------------------- particles
class Sparks:
    def __init__(self):
        self.p = np.zeros((0, 7), np.float32)  # x y vx vy life maxlife size

    def emit(self, xs, ys, n, speed=3.0, life=(0.5, 1.3), size=(1.0, 3.2)):
        if n <= 0 or len(xs) == 0:
            return
        idx = rng.integers(0, len(xs), n)
        ang = rng.uniform(0, 2 * np.pi, n)
        sp = rng.uniform(0.3, 1, n) * speed
        lf = rng.uniform(*life, n)
        new = np.stack([xs[idx] + rng.normal(0, 2, n), ys[idx] + rng.normal(0, 2, n),
                        np.cos(ang) * sp, np.sin(ang) * sp + 0.6, lf, lf,
                        rng.uniform(*size, n)], 1).astype(np.float32)
        self.p = np.concatenate([self.p, new])

    def step(self, dt):
        p = self.p
        p[:, 0] += p[:, 2]
        p[:, 1] += p[:, 3]
        p[:, 2] *= 0.95
        p[:, 3] = p[:, 3] * 0.95 + 0.06
        p[:, 4] -= dt
        self.p = p[p[:, 4] > 0]

    def draw(self):
        layer = np.zeros((H, W), np.float32)
        p = self.p
        if len(p):
            a = (p[:, 4] / p[:, 5]) ** 1.5
            flick = rng.uniform(0.5, 1, len(p))
            xi = np.clip(p[:, 0].astype(int), 0, W - 1)
            yi = np.clip(p[:, 1].astype(int), 0, H - 1)
            np.add.at(layer, (yi, xi), a * flick * p[:, 6] * 2.2)
        core = nd.gaussian_filter(layer, 1.2)
        halo = fast_bloom(layer, 10)
        return np.clip(core * 1.6, 0, 3) + halo * 6


# ---------------------------------------------------------------- frames
def render_video(path_noaudio):
    plate, s, oy = load_plate()
    mask, hp = logo_mask(plate, s, oy)
    ys, xs = np.nonzero(mask)
    top = np.argmin(ys)
    dist = geodesic(mask, (ys[top], xs[top]))
    # organic, slightly noisy reveal front
    noise = nd.gaussian_filter(rng.normal(0, 1, (H, W)), 6)
    dist = dist + noise / np.abs(noise).max() * 0.035

    soft = nd.gaussian_filter(mask.astype(np.float32), 3)
    edges = np.clip(np.abs(hp) / 30, 0, 1)  # follows the logo's own contours
    logo_layer = plate  # fully revealed frame == the original artwork
    # background glow with the mark inpainted (normalized convolution), so the
    # unrevealed logo never shows as a dark silhouette
    keep = 1 - nd.gaussian_filter(nd.binary_dilation(mask, iterations=6).astype(np.float32), 2)
    fill = blur(plate * keep[..., None], 45) / (nd.gaussian_filter(keep, 45)[..., None] + 1e-4)
    glow_layer = plate * keep[..., None] + fill * (1 - keep[..., None])
    cy, cx = ys.mean(), xs.mean()
    logo_lum = plate.mean(2) * soft

    tint_hot = np.array([0.80, 0.90, 1.0], np.float32)
    blue = np.array([0.25, 0.45, 1.0], np.float32)

    txt = render_text("قريباً", 150)
    t_h = txt.shape[0]
    t_y = int(oy + 1345 * s) - t_h // 2
    tcols = np.nonzero(txt.max(0) > 0.05)[0]
    tx0, tx1 = tcols.min(), tcols.max()

    sparks = Sparks()
    proc = None if PREVIEW is not None else subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
         "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", path_noaudio],
        stdin=subprocess.PIPE)

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    vign = np.clip(1 - (rad / (H * 0.75)) ** 2, 0, 1)[..., None]

    only = PREVIEW
    for i in range(N):
        t = i / FPS
        dt = 1 / FPS
        prog = ease_io((t - T_DRAW0) / (T_DRAW1 - T_DRAW0)) * 1.06
        width = 0.05
        revealed = np.clip((prog - dist) / width, 0, 1) * mask
        front = np.exp(-((dist - prog) / 0.022) ** 2) * mask * (prog < 1.05)

        # white-hot -> true colour settle after the hit
        settle = ease_out((t - T_HIT) / 1.1)
        hot = (1 - settle) * 0.85 * (t < T_HIT + 1.2)
        rev = nd.gaussian_filter(revealed, 4)[..., None]
        logo = logo_layer * rev
        lum = logo.mean(2, keepdims=True)
        h = hot * soft[..., None]
        logo = logo * (1 - h) + np.clip(lum * 2.2 + 0.08 * rev, 0, 1.2) * tint_hot * h

        # background glow builds with the drawing, punches at the hit
        g_amt = 0.15 + 0.85 * ease_out((t - T_DRAW0) / (T_HIT - T_DRAW0 + 0.4))
        frame = glow_layer * g_amt * (1 - rev) + logo

        # pen head
        pen = front * (0.6 + 1.2 * edges)
        pen_rgb = pen[..., None] * np.array([0.9, 0.95, 1.0])
        frame += pen_rgb * 1.3 + fast_bloom(pen_rgb, 14) * 3.0

        # sparks from the pen front
        if T_DRAW0 < t < T_DRAW1 + 0.05:
            fy, fx = np.nonzero(front[::3, ::3] > 0.5)
            sparks.emit(fx * 3.0, fy * 3.0, 45, speed=3.5)
        if abs(t - T_HIT) < dt / 2 + 1e-6:
            ey, ex = np.nonzero(mask[::4, ::4])
            sparks.emit(ex * 4.0, ey * 4.0, 900, speed=9, life=(0.6, 1.8), size=(0.8, 2.6))
        # ambient dust after the hit
        if t > T_HIT:
            sparks.emit(np.array([cx]), np.array([cy]), 2, speed=0, life=(1.5, 2.5), size=(0.5, 1.4))
            if len(sparks.p):
                sparks.p[-2:, 0] = rng.uniform(cx - 330, cx + 330, 2)
                sparks.p[-2:, 1] = rng.uniform(cy - 450, cy + 600, 2)
                sparks.p[-2:, 3] = rng.uniform(-1.2, -0.4, 2)
        sparks.step(dt)
        frame += sparks.draw()[..., None] * np.array([0.75, 0.85, 1.0])

        # impact flash + shockwave ring
        fl = np.exp(-max(t - T_HIT, 0) * 4.5) * (t >= T_HIT)
        if fl > 0.01:
            frame += fast_bloom(logo_lum[..., None] * np.array([0.7, 0.8, 1.0]), 40) * fl * 2.2
            r = (t - T_HIT) * 1400
            ring = np.exp(-((rad - r) / 18) ** 2) * fl * 0.55
            frame += ring[..., None] * blue

        # constant soft bloom on the revealed logo
        frame += fast_bloom(logo * soft[..., None], 30) * (0.35 + 0.4 * hot)

        # light sweep (glint) across the logo
        gp = (t - T_GLINT) / 0.9
        if 0 < gp < 1:
            band = (xx - cx) * 0.6 + (yy - cy) * 0.8
            pos = -700 + gp * 1500
            sweep = np.exp(-((band - pos) / 40) ** 2)
            frame += (sweep * logo_lum * 1.4)[..., None] * np.array([0.9, 0.95, 1.0])

        # ---- text "قريباً": right-to-left wipe with blur->sharp + rise
        tp = (t - T_TEXT0) / (T_TEXT1 - T_TEXT0)
        if tp > 0:
            e = ease_out(tp)
            # RTL wipe: reveal from the right edge
            edge_x = tx1 - (tx1 - tx0 + 80) * ease_io(tp * 1.15)
            cols = np.arange(W, dtype=np.float32)
            wipe = np.clip((cols - edge_x) / 60, 0, 1)[None, :]
            br = (1 - e) * 10
            ta = blur(txt, br) * wipe
            rise = int((1 - e) * 40)
            y0 = t_y + rise
            col = np.array([1.0, 1.0, 1.0])
            tl = np.zeros((H, W), np.float32)
            tl[y0:y0 + t_h] = ta
            # glowing leading edge
            lead = np.exp(-((cols - edge_x) / 22) ** 2)[None, :] * (tp < 1.05)
            tlead = np.zeros((H, W), np.float32)
            tlead[y0:y0 + t_h] = blur(txt, 3) * lead
            tg = tl + tlead * 1.2
            frame = frame * (1 - tl[..., None] * 0.9) + tl[..., None] * col
            frame += fast_bloom(tg[..., None] * np.array([0.5, 0.7, 1.0]), 18) * 1.6
            frame += tlead[..., None] * np.array([0.8, 0.9, 1.0])
            if 0 < tp < 1:
                ly = np.nonzero(txt.max(1) > 0.2)[0]
                sparks.emit(np.full(4, edge_x), y0 + rng.choice(ly, 4).astype(np.float32),
                            12, speed=2.5, life=(0.4, 1.0))
            # glint on the text too
            gp2 = (t - T_GLINT - 0.35) / 0.7
            if 0 < gp2 < 1:
                pos = tx0 + (tx1 - tx0 + 200) * gp2 - 100
                sw = np.exp(-((cols - pos) / 35) ** 2)[None, :]
                frame += (tl * sw * 0.9)[..., None] * np.array([0.6, 0.8, 1.0])

        # camera: slow push-in, slight drift
        z = 1.10 - 0.10 * ease_out(t / 4.0) + 0.012 * max(t - 4.0, 0) / 3.5
        shake = np.exp(-max(t - T_HIT, 0) * 9) * (t >= T_HIT) * 10
        frame = frame * (0.85 + 0.15 * vign)
        fade = ease_io(t / 0.35) * (1 - ease_io((t - T_OUT) / (DUR - T_OUT)))
        frame = 1 - np.exp(-np.clip(frame, 0, None) * 1.25)  # filmic tonemap
        frame *= fade

        img = Image.fromarray((np.clip(frame, 0, 1) * 255).astype(np.uint8))
        if abs(z - 1) > 1e-3 or shake > 0.1:
            dx = rng.normal(0, shake)
            dy = rng.normal(0, shake)
            img = img.transform((W, H), Image.AFFINE,
                                (1 / z, 0, cx - cx / z + dx, 0, 1 / z, cy - cy / z + dy),
                                resample=Image.BICUBIC)
        # gentle film grain
        arr = np.asarray(img, np.int16) + rng.integers(-3, 4, (H, W, 1))
        if only is not None:
            if i in only:
                Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(
                    os.path.join(OUT, f"preview_{i:03d}.png"))
            continue
        proc.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
        if i % 15 == 0:
            print(f"frame {i}/{N}", file=sys.stderr, flush=True)
    if proc:
        proc.stdin.close()
        proc.wait()


# ---------------------------------------------------------------- audio
def env_adsr(n, a, d, sus=0.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1) * np.exp(-np.maximum(t - a, 0) / d)
    return e + sus


def lp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), "low")
    return signal.lfilter(b, a, x)


def hp_(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), "high")
    return signal.lfilter(b, a, x)


def bp_sweep(noise, f0, f1, q=2.0, block=512):
    """Band-pass noise with a moving centre frequency (whoosh)."""
    out = np.zeros_like(noise)
    nb = len(noise) // block + 1
    zi = None
    for k in range(nb):
        seg = noise[k * block:(k + 1) * block]
        if not len(seg):
            break
        fc = f0 * (f1 / f0) ** (k / max(nb - 1, 1))
        bw = fc / q
        lo, hi = max(fc - bw / 2, 20), min(fc + bw / 2, SR / 2 - 100)
        b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        y, zi = signal.lfilter(b, a, seg, zi=zi)
        out[k * block:(k + 1) * block] = y
    return out


def place(buf, x, t0, pan=0.0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 >= buf.shape[0]:
        return
    x = x[:buf.shape[0] - i0]
    l = np.cos((pan + 1) * np.pi / 4)
    r = np.sin((pan + 1) * np.pi / 4)
    buf[i0:i0 + len(x), 0] += x * gain * l * 1.414
    buf[i0:i0 + len(x), 1] += x * gain * r * 1.414


def make_reverb(seconds=2.8):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.stack([rng.normal(0, 1, n), rng.normal(0, 1, n)], 1) * np.exp(-t / 0.55)[:, None]
    ir = np.stack([lp(ir[:, c], 7000) for c in range(2)], 1)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))


def render_audio(path):
    n = int((DUR + 0.5) * SR)
    dry = np.zeros((n, 2))
    send = np.zeros((n, 2))
    tt = lambda d: np.arange(int(d * SR)) / SR

    # 1. dark atmospheric drone + riser into the hit
    d = T_HIT
    t = tt(d)
    f = 55 * (2 ** (t / d * 1.0))
    drone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    drone *= (t / d) ** 2 * 0.18
    place(dry, drone, 0)
    riser = bp_sweep(rng.normal(0, 1, len(t)), 300, 6000, q=3) * (t / d) ** 3
    place(dry, riser, 0, pan=-0.2, gain=0.35)
    place(send, riser, 0, pan=0.2, gain=0.35)

    # 2. pen whoosh following the drawing
    d = T_DRAW1 - T_DRAW0 + 0.2
    t = tt(d)
    w = bp_sweep(rng.normal(0, 1, len(t)), 2500, 500, q=1.5)
    w *= np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5 * (0.7 + 0.3 * np.sin(2 * np.pi * 3 * t))
    pan_lfo = np.sin(2 * np.pi * 0.6 * t) * 0.5
    place(dry, w * (1 - pan_lfo) * 0.5, T_DRAW0, pan=-0.5, gain=0.5)
    place(dry, w * (1 + pan_lfo) * 0.5, T_DRAW0, pan=0.5, gain=0.5)
    place(send, w, T_DRAW0, gain=0.25)

    # 3. sparkle / glitter pings during drawing and text
    def ping(f, dur=0.25, amp=1.0):
        tp = tt(dur)
        x = np.sin(2 * np.pi * f * tp) + 0.3 * np.sin(2 * np.pi * f * 2.76 * tp)
        return x * env_adsr(len(tp), 0.002, dur / 5) * amp

    for tk in np.sort(rng.uniform(T_DRAW0, T_DRAW1, 70)):
        p = ping(rng.uniform(3500, 9000), amp=rng.uniform(0.02, 0.06))
        pan = rng.uniform(-0.8, 0.8)
        place(dry, p, tk, pan=pan)
        place(send, p, tk, pan=-pan, gain=0.8)

    # 4. IMPACT: sub boom + punch + noise crack + metallic shimmer tail
    t = tt(2.5)
    fsub = 40 + 110 * np.exp(-t / 0.05)
    sub = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env_adsr(len(t), 0.002, 0.65)
    place(dry, np.tanh(sub * 2.2) * 0.75, T_HIT)
    crack = hp_(rng.normal(0, 1, int(0.4 * SR)), 900) * env_adsr(int(0.4 * SR), 0.001, 0.06)
    place(dry, crack, T_HIT, gain=0.35)
    place(send, crack, T_HIT, gain=0.6)
    # inharmonic shimmer (bell-like partials) on the hit
    t = tt(3.0)
    shim = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / dcy) * a
               for f, dcy, a in [(523.25, 1.4, .30), (784, 1.1, .22), (1046.5, 0.9, .18),
                                 (1567.98, 0.7, .12), (2093, 0.5, .08), (2637, 0.4, .06)])
    shim *= np.minimum(t / 0.004, 1)
    place(dry, shim, T_HIT, pan=-0.1, gain=0.22)
    place(send, shim, T_HIT, pan=0.1, gain=0.45)
    # reverse-swell into the hit
    t = tt(0.6)
    rev = bp_sweep(rng.normal(0, 1, len(t)), 800, 4000, q=1.2) * (t / 0.6) ** 4
    place(dry, rev, T_HIT - 0.6, gain=0.4)

    # 5. text reveal: airy swish + warm chord pad with soft chime
    d = T_TEXT1 - T_TEXT0 + 0.3
    t = tt(d)
    sw = bp_sweep(rng.normal(0, 1, len(t)), 6000, 1500, q=2) * np.sin(np.pi * t / d) ** 2
    place(dry, sw, T_TEXT0, pan=0.4, gain=0.25)
    place(send, sw, T_TEXT0, pan=-0.4, gain=0.3)
    t = tt(4.0)
    pad = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2 * t + 0.4)
              for f in [130.81, 196.0, 261.63, 329.63, 392.0])
    pad *= np.minimum(t / 0.8, 1) * np.exp(-np.maximum(t - 1.5, 0) / 1.2)
    place(dry, lp(pad, 2500), T_TEXT0, gain=0.035)
    place(send, lp(pad, 2500), T_TEXT0, gain=0.05)
    for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):  # arpeggiated chime, RTL
        c = ping(f, dur=1.6, amp=0.11)
        place(dry, c, T_TEXT0 + 0.12 + k * 0.17, pan=0.6 - k * 0.4)
        place(send, c, T_TEXT0 + 0.12 + k * 0.17, gain=1.2)

    # 6. glint sweep "shing"
    t = tt(0.9)
    g = bp_sweep(rng.normal(0, 1, len(t)), 4000, 11000, q=4) * np.sin(np.pi * t / 0.9) ** 3
    place(dry, g, T_GLINT, pan=-0.3, gain=0.22)
    place(send, g, T_GLINT, pan=0.3, gain=0.3)
    for tk in np.sort(rng.uniform(T_GLINT, T_GLINT + 0.9, 14)):
        p = ping(rng.uniform(5000, 10000), amp=0.03)
        place(send, p, tk, pan=rng.uniform(-1, 1))

    # 7. low tail swell for the outro
    t = tt(DUR - T_HIT)
    tail = lp(rng.normal(0, 1, len(t)), 200) * np.exp(-t / 1.6) * 0.5
    place(dry, tail, T_HIT, gain=0.6)

    ir = make_reverb()
    wet = np.stack([signal.fftconvolve(send[:, c], ir[:, c])[:n] for c in range(2)], 1)
    mix = dry + wet * 0.9
    mix = np.stack([hp_(mix[:, c], 28) for c in range(2)], 1)
    mix /= np.abs(mix).max()
    mix = np.tanh(mix * 1.6) / np.tanh(1.6)  # glue / soft limit
    fade_n = int(0.5 * SR)
    mix[-fade_n:] *= np.linspace(1, 0, fade_n)[:, None]
    pcm = (mix * 0.89 * 32767).astype(np.int16)
    import wave
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(OUT, "sfx.wav")
    vid = os.path.join(OUT, "_video.mp4")
    render_audio(wav)
    if "--audio-only" in sys.argv:
        return
    if "--preview" in sys.argv:
        global PREVIEW
        PREVIEW = set(range(0, N, 15))
        render_video(os.devnull)
        return
    render_video(vid)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", wav,
                    "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart",
                    os.path.join(OUT, "coming_soon.mp4")], check=True)
    os.remove(vid)


if __name__ == "__main__":
    main()
