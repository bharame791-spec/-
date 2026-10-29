"""RAM logo reveal in the style of the Al Jazeera "قريباً" reference, with sound design.

Scene: full-screen royal blue.  The logo is rebuilt in glowing white from the
clean artwork, split into its real layers.  The camera starts pushed in and keeps
creeping in while every layer trim-paths on (thin white stroke first, fill
chasing it, sparks at the heads).  When the logo completes it flashes and the
camera snaps back out with motion blur.  Then the divider grows and "RAM" /
"رام" slide out of it, the subtitle wipes in, the quotes pop and "قريباً"
types in right to left.

Usage:
    python3 src/render.py            -> out/coming_soon.mp4
    python3 src/render.py --preview  -> out/preview_###.png
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
DUR = 7.2
SR = 48000
N = int(DUR * FPS)

# ---- timeline (seconds)
# (start, end) of each layer's outline stroke; the fill chases it FILL_LAG behind
T_LAYERS = [(0.15, 0.80),   # top ribbon
            (0.30, 1.15),   # second ribbon -> ring -> arrow head -> outer crescent
            (0.55, 1.00)]   # grey inner crescent
FILL_LAG = 0.12
FILL_SPEED = 1.2
T_FLASH = 1.30              # logo complete: flash + camera snaps out
T_ZOOM_OUT = (1.22, 1.95)
T_BAR = 2.00                # divider bar grows, "RAM" and "رام" slide out of it
T_SUB = 2.55                # subtitle wipes in right to left
T_QUOTES = 3.25
T_SOON0, T_SOON1 = 3.40, 4.20   # "قريباً" types in
T_GLINT = 4.85
T_OUT = 6.6

# ---- layout (world space == output frame at zoom 1); full-screen blue, no card
LOGO_H = 540                    # logo height
LOGO_CY = 770
SOON_GAP = 150                  # from the subtitle's baseline to the centre of "قريباً"

rng = np.random.default_rng(7)
PREVIEW = None


def clamp01(x):
    return np.clip(x, 0, 1)


def ease_out(x):
    return 1 - (1 - clamp01(x)) ** 3


def ease_io(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def ease_out_expo(x):
    x = clamp01(x)
    return np.where(x >= 1, 1.0, 1 - 2 ** (-10 * x))


def ease_in(x):
    return clamp01(x) ** 2


def blur(a, r):
    if r < 0.3:
        return a
    if a.ndim == 3:
        return np.stack([nd.gaussian_filter(a[..., c], r) for c in range(a.shape[2])], -1)
    return nd.gaussian_filter(a, r)


def bloom(img, r, f=4):
    """Wide blur via downscale (cheap glow)."""
    small = img[::f, ::f]
    b = blur(small, r / f)
    up = np.repeat(np.repeat(b, f, 0), f, 1)
    return up[:img.shape[0], :img.shape[1]]


def over(frame, color, alpha):
    a = alpha[..., None] if alpha.ndim == 2 else alpha
    return frame * (1 - a) + color * a


# ---------------------------------------------------------------- logo from artwork
def extract_logo():
    """Masks + shading of the three logo layers and the name/subtitle, placed in world space."""
    art = np.asarray(Image.open(os.path.join(ASSETS, "logo_clean.png")).convert("RGB"), np.float32)
    r, g, b = art[..., 0], art[..., 1], art[..., 2]
    lum = (r + g + b) / 3
    blue = (b - r > 40) & (lum < 200)
    grey = (np.abs(b - r) < 60) & (lum < 190) & (lum > 100) & ~blue
    zone = np.arange(art.shape[0])[:, None] < 920
    lab, n = nd.label(blue & zone)
    sizes = nd.sum(np.ones_like(lab), lab, range(1, n + 1))
    order = np.argsort(sizes)[::-1]
    comps = [lab == order[k] + 1 for k in range(2)]
    comps.sort(key=lambda m: np.nonzero(m)[0].min())
    glab, gn = nd.label(grey & zone)
    comps.append(glab == np.argmax(nd.sum(np.ones_like(glab), glab, range(1, gn + 1))) + 1)

    allm = comps[0] | comps[1] | comps[2]
    ys, xs = np.nonzero(allm)
    pad = 6
    y0, y1 = ys.min() - pad, ys.max() + pad
    tys, txs = np.nonzero((blue | grey)[920:1080])
    x0, x1 = min(xs.min(), txs.min()) - pad, max(xs.max(), txs.max()) + pad
    s = LOGO_H / (y1 - y0)
    tw, th = round((x1 - x0) * s), round((y1 - y0) * s)
    ox, oy = W // 2 - tw // 2, LOGO_CY - th // 2

    def place(a, r0=y0, r1=y1):
        rh = round((r1 - r0) * s)
        im = Image.fromarray(a[r0:r1, x0:x1].astype(np.float32), "F").resize((tw, rh), Image.BILINEAR)
        out = np.zeros((H, W), np.float32)
        top = oy + round((r0 - y0) * s)
        out[top:top + rh, ox:ox + tw] = np.asarray(im)
        return out

    masks = [clamp01(place(nd.gaussian_filter(m.astype(np.float32), 0.7))) for m in comps]
    # shading: lighter bands of the original read whiter, darker bands slightly blue
    shade = np.zeros_like(lum)
    for m, (lo, hi) in zip(comps, [(25, 110), (25, 110), (120, 190)]):
        shade[m] = clamp01((lum[m] - lo) / (hi - lo))
    shade = place(nd.grey_dilation(shade, size=3))

    # the name "RAM | رام" and the subtitle, kept exactly where the artwork has them
    rows = np.arange(art.shape[0])[:, None]
    ink = (blue | grey) & (rows >= 920) & (rows < 1080)
    ink[:, :x0] = False
    ink[:, x1:] = False
    t0, t1 = 920, 1080
    soft = nd.gaussian_filter(ink.astype(np.float32), 0.6)
    title = clamp01(place(soft * (rows < 1015), t0, t1) * 1.3)
    subtitle = clamp01(place(soft * (rows >= 1015), t0, t1) * 1.3)
    return masks, shade, title, subtitle


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


# ---------------------------------------------------------------- scene pieces
def make_background():
    """Full-screen royal blue, brighter behind the logo, gently darker at the edges."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / 760) ** 2 + ((yy - LOGO_CY) / 1050) ** 2)
    col = (np.array([0.12, 0.23, 0.74])[None, None]
           + clamp01(1 - d)[..., None] ** 1.5 * np.array([0.13, 0.15, 0.17]))
    vign = clamp01(1 - ((xx - W / 2) ** 2 / (W * 1.1) ** 2 + (yy - H / 2) ** 2 / (H * 0.85) ** 2))
    return col * (0.70 + 0.30 * vign[..., None])


def render_text(word, size):
    ar = ImageFont.truetype(os.path.join(ASSETS, "cairo-arabic-800-normal.woff"), size)
    qf = ImageFont.truetype("DejaVuSans-Bold.ttf", int(size * 0.62))
    word_img = Image.new("L", (W, size * 2), 0)
    q_img = Image.new("L", (W, size * 2), 0)
    d = ImageDraw.Draw(word_img)
    d.text((W // 2, size), word, font=ar, fill=255, anchor="mm", direction="rtl", language="ar")
    l, t, r, b = d.textbbox((W // 2, size), word, font=ar, anchor="mm", direction="rtl", language="ar")
    dq = ImageDraw.Draw(q_img)
    dq.text((r + size * 0.05, t + size * 0.02), '"', font=qf, fill=255, anchor="lt")
    dq.text((l - size * 0.05, t + size * 0.02), '"', font=qf, fill=255, anchor="rt")
    return (np.asarray(word_img, np.float32) / 255, np.asarray(q_img, np.float32) / 255, l, r)


class Sparks:
    def __init__(self):
        self.p = np.zeros((0, 7), np.float32)  # x y vx vy life maxlife size

    def emit(self, xs, ys, n, speed=3.0, life=(0.3, 0.9), size=(1.0, 3.0)):
        if n <= 0 or len(xs) == 0:
            return
        idx = rng.integers(0, len(xs), n)
        ang = rng.uniform(0, 2 * np.pi, n)
        sp = rng.uniform(0.2, 1, n) * speed
        lf = rng.uniform(*life, n)
        new = np.stack([xs[idx] + rng.normal(0, 3, n), ys[idx] + rng.normal(0, 3, n),
                        np.cos(ang) * sp, np.sin(ang) * sp + 0.8, lf, lf,
                        rng.uniform(*size, n)], 1).astype(np.float32)
        self.p = np.concatenate([self.p, new])

    def step(self, dt):
        p = self.p
        p[:, 0] += p[:, 2]
        p[:, 1] += p[:, 3]
        p[:, 2] *= 0.93
        p[:, 3] = p[:, 3] * 0.93 + 0.12
        p[:, 4] -= dt
        self.p = p[p[:, 4] > 0]

    def draw(self):
        layer = np.zeros((H, W), np.float32)
        p = self.p
        if len(p):
            a = (p[:, 4] / p[:, 5]) ** 1.2 * rng.uniform(0.5, 1, len(p))
            xi = np.clip(p[:, 0].astype(int), 0, W - 1)
            yi = np.clip(p[:, 1].astype(int), 0, H - 1)
            np.add.at(layer, (yi, xi), a * p[:, 6] * 2.5)
        return clamp01(nd.gaussian_filter(layer, 1.1) * 1.8) + bloom(layer, 8) * 4


# ---------------------------------------------------------------- frames
def camera(t):
    """Zoom and focus point: push in while drawing, snap out at the flash, then drift."""
    z_draw = 1.30 + 0.32 * ease_in(t / T_ZOOM_OUT[0])
    zo = ease_out_expo((t - T_ZOOM_OUT[0]) / (T_ZOOM_OUT[1] - T_ZOOM_OUT[0]))
    z = z_draw + (1.07 - z_draw) * zo
    z -= 0.06 * ease_io((t - T_ZOOM_OUT[1]) / (DUR - T_ZOOM_OUT[1]))
    fy = LOGO_CY - 140 + 140 * ease_io(t / 1.2)          # follow the drawing down
    fy = fy + (H / 2 - fy) * zo                           # recentre on the frame
    half = H / 2 / max(z, 1.0)
    fy = float(np.clip(fy, half, H - half))               # never look past the background
    return z, W / 2, fy


def render_video(path_noaudio):
    masks, shade, title, subtitle = extract_logo()
    union = clamp01(sum(masks))
    layers = []
    taken = np.zeros((H, W), bool)
    for m in masks:
        mb = (m > 0.02) & ~taken
        taken |= mb
        ys, xs = np.nonzero(m > 0.5)
        k = np.argmin(ys)
        dist = geodesic(mb, (ys[k], xs[k]))
        hard = m > 0.5
        edge = nd.binary_dilation(hard, iterations=2) & ~nd.binary_erosion(hard, iterations=1)
        layers.append((m, dist, nd.gaussian_filter(edge.astype(np.float32), 0.6)))
    ys, xs = np.nonzero(union > 0.5)
    lcx, lcy = xs.mean(), ys.mean()
    logo_rgb = (np.array([0.90, 0.94, 1.0])[None, None] * (1 - shade[..., None])
                + np.array([1.0, 1.0, 1.0])[None, None] * shade[..., None])
    logo_rgb[masks[2] > 0.1] = logo_rgb[masks[2] > 0.1] * 0.92

    background = make_background()
    cols = np.arange(W, dtype=np.float32)
    rows = np.arange(H, dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # name: split at the divider bar
    tys, txs = np.nonzero(title > 0.5)
    tcols = np.nonzero((title > 0.5).sum(0))[0]
    groups = np.split(tcols, np.nonzero(np.diff(tcols) > 3)[0] + 1)
    mid = (txs.min() + txs.max()) / 2
    bar = min(groups, key=lambda g: abs(g.mean() - mid) + 1000 * (len(g) > 25))
    bar_x0, bar_x1 = bar.min() - 2, bar.max() + 3
    bar_y0, bar_y1 = tys.min(), tys.max()
    sys_, sxs = np.nonzero(subtitle > 0.5)
    sub_x0, sub_x1 = sxs.min(), sxs.max()

    word, quotes, wl, wr = render_text("قريباً", 112)
    t_h = word.shape[0]
    t_y = int(sys_.max() + SOON_GAP) - t_h // 2

    sparks = Sparks()
    proc = None
    if PREVIEW is None:
        proc = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
             "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", path_noaudio],
            stdin=subprocess.PIPE)

    dt = 1 / FPS
    for i in range(N):
        t = i / FPS
        world = background.copy()

        # ---- logo: per layer, white stroke traces first, fill chases it
        fill = np.zeros((H, W), np.float32)
        stroke = np.zeros((H, W), np.float32)
        head = np.zeros((H, W), np.float32)
        for (m, dist, edge), (t0, t1) in zip(layers, T_LAYERS):
            ps = ease_out((t - t0) / (t1 - t0))
            if ps <= 0:
                continue
            ps *= 1.02
            f0 = t0 + FILL_LAG
            pf = ease_io((t - f0) / ((t1 - t0) / FILL_SPEED)) * 1.03
            done = f0 + (t1 - t0) / FILL_SPEED
            stroke += clamp01((ps - dist) / 0.01) * edge * (1 - ease_io((t - done) / 0.2))
            fill += clamp01((pf - dist) / 0.015) * m
            if ps < 1.02:
                h_ = np.exp(-((dist - ps) / 0.018) ** 2) * edge * (dist <= ps + 0.004)
                head += h_
                hy, hx = np.nonzero(h_[::3, ::3] > 0.4)
                sparks.emit(hx * 3.0, hy * 3.0, 14, speed=4.0)
        fill = clamp01(fill)
        logo_a = clamp01(fill + stroke)
        logo_col = over(np.ones((H, W, 3)), logo_rgb, fill / np.maximum(logo_a, 1e-4))

        # glow: steady halo + flash bloom at completion
        fl = np.exp(-max(t - T_FLASH, 0) * 3.2) * (t >= T_FLASH)
        pre = ease_in((t - 0.9) / (T_FLASH - 0.9)) * (t < T_FLASH)
        glow_amt = 0.95 + 0.9 * fl + 0.6 * pre
        src = logo_a[..., None] * logo_col
        world += bloom(src, 18) * 0.55 * glow_amt * np.array([0.75, 0.85, 1.0])
        world += bloom(src, 60) * 0.65 * glow_amt * np.array([0.55, 0.70, 1.0])
        world = over(world, logo_col, logo_a)
        if fl > 0.01:  # overexposed core during the flash
            world += src * fl * 1.2
            world += bloom(src, 40) * fl * 1.6 * np.array([0.75, 0.85, 1.0])
            world += bloom(src, 120) * fl * 0.9 * np.array([0.6, 0.72, 1.0])
        if head.any():
            world += bloom(head[..., None] * np.ones(3), 10) * 3.0 * np.array([0.8, 0.9, 1.0])
            world += nd.gaussian_filter(head, 1.2)[..., None] * 1.2

        # sparks: from the trim heads, plus a burst at the flash
        if abs(t - T_FLASH) < dt / 2 + 1e-6:
            ey, ex = np.nonzero(union[::4, ::4] > 0.5)
            sparks.emit(ex * 4.0, ey * 4.0, 700, speed=8, life=(0.5, 1.4), size=(0.8, 2.4))
        if t > T_FLASH and i % 2 == 0:  # floating dust
            sparks.emit(np.array([lcx]), np.array([lcy]), 1, speed=0, life=(1.2, 2.2), size=(0.5, 1.3))
            sparks.p[-1, 0] = rng.uniform(60, W - 60)
            sparks.p[-1, 1] = rng.uniform(300, H - 300)
            sparks.p[-1, 3] = rng.uniform(-1.0, -0.3)
        sparks.step(dt)
        world += sparks.draw()[..., None] * np.array([0.85, 0.92, 1.0])

        # ---- name: divider grows, then "RAM" / "رام" slide out from behind it
        txt = np.zeros((H, W), np.float32)
        bp = ease_out((t - T_BAR) / 0.3)
        if bp > 0:
            ymid = (bar_y0 + bar_y1) / 2
            half = (bar_y1 - bar_y0) / 2 * bp + 1
            bm = np.zeros((H, W), np.float32)
            bm[:, bar_x0:bar_x1] = clamp01(half + 1 - np.abs(rows - ymid))[:, None]
            txt += bm * title
        npg = ease_out((t - T_BAR - 0.15) / 0.7)
        if npg > 0:
            shift = int(round((1 - npg) * 160))
            for side, sgn in ((xx >= bar_x1, -1), (xx < bar_x0, 1)):
                txt += np.roll(title * side, sgn * shift, 1) * side * clamp01(npg * 1.8)
        sp = (t - T_SUB) / 0.75
        if sp > 0:
            edge = sub_x1 + 20 - (sub_x1 - sub_x0 + 110) * ease_io(sp)
            txt += clamp01((cols - edge) / 45)[None, :] * subtitle
        if bp > 0:
            txt = clamp01(txt)
            world += bloom(txt[..., None] * np.ones(3), 14) * 0.8 * np.array([0.6, 0.75, 1.0])
            world = over(world, np.ones(3), txt)

        # ---- quotes pop, then "قريباً" types in right to left
        qp = ease_out((t - T_QUOTES) / 0.25)
        if qp > 0:
            ql = np.zeros((H, W), np.float32)
            ql[t_y:t_y + t_h] = quotes * qp
            world += bloom(ql[..., None] * np.ones(3), 14) * 0.6 * np.array([0.6, 0.75, 1.0])
            world = over(world, np.ones(3), ql)
        tp = (t - T_SOON0) / (T_SOON1 - T_SOON0)
        if tp > 0:
            edge_x = wr - (wr - wl + 30) * clamp01(tp)
            wipe = clamp01((cols - edge_x) / 18)[None, :]
            tl = np.zeros((H, W), np.float32)
            tl[t_y:t_y + t_h] = word * wipe
            lead = np.zeros((H, W), np.float32)
            lead[t_y:t_y + t_h] = blur(word, 2) * np.exp(-((cols - edge_x) / 14) ** 2)[None, :] * (tp < 1)
            world += bloom((tl + lead * 2)[..., None] * np.ones(3), 16) * 1.0 * np.array([0.6, 0.75, 1.0])
            world = over(world, np.ones(3), tl)
            world += lead[..., None] * 0.8
            if 0 < tp < 1:
                ly = np.nonzero(word.max(1) > 0.3)[0]
                sparks.emit(np.full(3, edge_x), t_y + rng.choice(ly, 3).astype(np.float32), 6,
                            speed=2.5, life=(0.3, 0.7))
            gp = (t - T_GLINT) / 0.6
            if 0 < gp < 1:  # light sweep over logo and word
                band = (xx - W / 2) * 0.5 + (yy - LOGO_CY) * 0.86
                pos = -420 + gp * 1100
                sw = np.exp(-((band - pos) / 30) ** 2)
                world += (sw * (union + tl + txt) * 0.6)[..., None] * np.array([0.9, 0.95, 1.0])

        # ---- camera (with motion blur while it snaps out)
        world = np.clip(world, 0, None)  # soft shoulder only above 0.8
        world = np.where(world < 0.8, world, 0.8 + 0.2 * (1 - np.exp(-(world - 0.8) / 0.2)))
        wimg = Image.fromarray((np.clip(world, 0, 1) * 255).astype(np.uint8))
        z0, fx, fy = camera(t)
        z1, _, fy1 = camera(t + dt * 0.8)
        nsub = 1 + int(min(abs(z1 - z0) / z0 * 40, 7))
        acc = np.zeros((H, W, 3), np.float32)
        for k in range(nsub):
            a = k / max(nsub - 1, 1) if nsub > 1 else 0
            z = z0 + (z1 - z0) * a
            f = fy + (fy1 - fy) * a
            sh = rng.normal(0, 1, 2) * 6 * np.exp(-max(t - T_FLASH, 0) * 10) * (t >= T_FLASH)
            im = wimg.transform((W, H), Image.AFFINE,
                                (1 / z, 0, fx - (W / 2) / z + sh[0], 0, 1 / z, f - (H / 2) / z + sh[1]),
                                resample=Image.BICUBIC, fillcolor=(20, 38, 120))
            acc += np.asarray(im, np.float32)
        frame = acc / nsub
        # white flash over the whole frame for a few frames
        if fl > 0.01:
            frame = frame + (255 - frame) * (fl ** 4) * 0.10
        fade = ease_io(t / 0.25) * (1 - ease_io((t - T_OUT) / (DUR - T_OUT)))
        arr = np.clip(frame * fade + rng.normal(0, 1.6, (H, W, 1)), 0, 255).astype(np.uint8)
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

    # tension: low drone + riser climbing into the flash
    t = secs(T_FLASH)
    f = 55 * 2 ** (t / T_FLASH)
    drone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    place(dry, drone * (t / T_FLASH) ** 1.5 * 0.18, 0)
    riser = bp_sweep(rng.normal(0, 1, len(t)), 300, 7000, q=3) * (t / T_FLASH) ** 2.5
    place(dry, riser, 0, pan=-0.25, gain=0.32)
    place(send, riser, 0, pan=0.25, gain=0.35)

    # a fast whoosh per trim-path layer, panned along the stroke, with glitter
    for (t0, t1), (f0, f1), pans in zip(
            T_LAYERS, [(3500, 800), (2800, 500), (4500, 1600)],
            [(-0.2, 0.6), (0.5, -0.6), (0.4, -0.3)]):
        d = t1 - t0 + 0.2
        w = whoosh(d, f0, f1, shape=1.2)
        pan = np.linspace(*pans, len(w))
        place(dry, w, t0 - 0.03, pan=pan, gain=0.45)
        place(send, w, t0 - 0.03, pan=-pan, gain=0.25)
        for s_ in np.sort(rng.uniform(t0, t1 + 0.1, 26)):
            p = ping(rng.uniform(4000, 10000), dur=0.2, amp=rng.uniform(0.015, 0.045))
            place(dry, p, s_, pan=rng.uniform(-0.9, 0.9))
            place(send, p, s_, pan=rng.uniform(-0.9, 0.9), gain=0.8)

    # FLASH: reverse swell -> sub boom + crack + bell shimmer, big whoosh for the zoom out
    t = secs(0.5)
    place(dry, bp_sweep(rng.normal(0, 1, len(t)), 600, 5000, q=1.2) * (t / 0.5) ** 4,
          T_FLASH - 0.5, gain=0.4)
    t = secs(2.6)
    fsub = 40 + 110 * np.exp(-t / 0.05)
    sub = np.sin(2 * np.pi * np.cumsum(fsub) / SR) * env(len(t), 0.002, 0.7)
    place(dry, np.tanh(sub * 2.2) * 0.8, T_FLASH)
    crack = hp(rng.normal(0, 1, int(0.4 * SR)), 900) * env(int(0.4 * SR), 0.001, 0.06)
    place(dry, crack, T_FLASH, gain=0.32)
    place(send, crack, T_FLASH, gain=0.6)
    shim = bell([(523.25, 1.4, .30), (784, 1.1, .22), (1046.5, 0.9, .18),
                 (1567.98, 0.7, .12), (2093, 0.5, .08), (2637, 0.4, .06)], 3.2)
    place(dry, shim, T_FLASH, pan=-0.1, gain=0.22)
    place(send, shim, T_FLASH, pan=0.1, gain=0.45)
    d = T_ZOOM_OUT[1] - T_ZOOM_OUT[0] + 0.3
    zw = whoosh(d, 1800, 220, q=1.0, shape=0.8) * np.exp(-secs(d) / 0.35)
    place(dry, zw, T_ZOOM_OUT[0], pan=-0.3, gain=0.6)
    place(dry, whoosh(d, 1700, 200, q=1.0, shape=0.8) * np.exp(-secs(d) / 0.35),
          T_ZOOM_OUT[0], pan=0.3, gain=0.6)
    place(send, zw, T_ZOOM_OUT[0], gain=0.3)
    t = secs(DUR - T_FLASH)                                  # low tail
    place(dry, lp(rng.normal(0, 1, len(t)), 180) * np.exp(-t / 1.5), T_FLASH, gain=0.35)

    # divider: soft tick, then a stereo split swish as the names slide out
    tk = lp(hp(rng.normal(0, 1, int(0.05 * SR)), 1500), 6000) * env(int(0.05 * SR), 0.0005, 0.01)
    place(dry, tk, T_BAR, gain=0.35)
    place(send, tk, T_BAR, gain=0.35)
    sw = whoosh(0.7, 5500, 1800, q=2, shape=2)
    place(dry, sw, T_BAR + 0.12, pan=np.linspace(0, -0.8, len(sw)), gain=0.22)
    place(dry, whoosh(0.7, 5200, 1700, q=2, shape=2), T_BAR + 0.12,
          pan=np.linspace(0, 0.8, len(sw)), gain=0.22)
    place(send, sw, T_BAR + 0.12, gain=0.15)
    sw = whoosh(0.8, 7000, 3000, q=2.5, shape=2)            # subtitle wipe
    place(dry, sw, T_SUB, pan=np.linspace(0.6, -0.6, len(sw)), gain=0.14)
    place(send, sw, T_SUB, gain=0.1)

    # quotes: two soft pops
    for k, pan in enumerate((0.5, -0.5)):
        pp = np.sin(2 * np.pi * 900 * secs(0.08)) * env(int(0.08 * SR), 0.001, 0.015)
        place(dry, pp, T_QUOTES + k * 0.06, pan=pan, gain=0.18)
        place(send, pp, T_QUOTES + k * 0.06, gain=0.25)

    # "قريباً": airy swish right->left, typing ticks, warm pad + chime arpeggio
    d = T_SOON1 - T_SOON0 + 0.3
    sw = whoosh(d, 6500, 1600, q=2, shape=2)
    place(dry, sw, T_SOON0, pan=np.linspace(0.6, -0.6, len(sw)), gain=0.2)
    place(send, sw, T_SOON0, gain=0.25)
    for k in range(6):
        tk = hp(rng.normal(0, 1, int(0.025 * SR)), 3000) * env(int(0.025 * SR), 0.0005, 0.005)
        place(dry, tk, T_SOON0 + k * (T_SOON1 - T_SOON0) / 6, pan=0.5 - k * 0.2, gain=0.16)
    t = secs(3.6)
    pad = sum(np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.4)
              for f in [130.81, 196.0, 261.63, 329.63, 392.0])
    pad = lp(pad * np.minimum(t / 0.7, 1) * np.exp(-np.maximum(t - 1.5, 0) / 1.1), 2500)
    place(dry, pad, T_SOON0, gain=0.03)
    place(send, pad, T_SOON0, gain=0.045)
    for k, f in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        c = ping(f, dur=1.6, amp=0.10)
        place(dry, c, T_SOON0 + 0.1 + k * 0.17, pan=0.6 - k * 0.4)
        place(send, c, T_SOON0 + 0.1 + k * 0.17, gain=1.2)
    g = whoosh(0.6, 4500, 11000, q=4, shape=3)              # glint
    place(dry, g, T_GLINT, pan=np.linspace(-0.4, 0.4, len(g)), gain=0.16)
    place(send, g, T_GLINT, gain=0.22)
    for s_ in np.sort(rng.uniform(T_GLINT, T_GLINT + 0.6, 8)):
        place(send, ping(rng.uniform(6000, 10000), amp=0.03), s_, pan=rng.uniform(-1, 1))

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
        PREVIEW = set(range(3, 60, 4)) | set(range(60, N, 15))
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
