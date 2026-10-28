"""RAM | رام — round 6: folded-ribbon calligraphy (after the «حرية» reference).

Each letter is a broad-nib stroke: a flat pen of width L at angle φ is swept along a
Catmull-Rom centreline. Where the path runs parallel to the nib the stroke collapses
and flips, which gives the twisted-ribbon look; front and back faces are shaded
differently and each sweep is split into bands across the nib for a curved surface.
"""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out6")
os.makedirs(OUT, exist_ok=True)


def catmull(pts, per=40):
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i-1], P[i], P[i+1], P[i+2]
        for k in range(per):
            t = k / per
            t2, t3 = t*t, t*t*t
            out.append(tuple(0.5*((2*p1[j]) + (-p0[j]+p2[j])*t + (2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2
                                  + (-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def lerp(a, b, t):
    return a + (b - a)*t


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return "#" + "".join(f"{round(lerp(int(c1[i:i+2], 16), int(c2[i:i+2], 16), t)):02x}" for i in (1, 3, 5))


def interp(stops, t):
    """Piecewise-linear value from [(t, v), …]."""
    for (t0, v0), (t1, v1) in zip(stops, stops[1:]):
        if t <= t1:
            return lerp(v0, v1, (t - t0)/(t1 - t0) if t1 > t0 else 0)
    return stops[-1][1]


def ribbon(pts, L, phi, taper, pal, bands=10, per=40):
    """pts: centreline; phi: [(t, deg)] nib angle; taper: [(t, k)] width factor; pal: palette dict."""
    c = catmull(pts, per)
    n = len(c)
    o = []
    prev = None
    for i in range(n):
        t = i/(n-1)
        a = math.radians(interp(phi, t))
        w = L*interp(taper, t)
        nx, ny = math.cos(a)*w/2, -math.sin(a)*w/2
        x, y = c[i]
        edge = [(x - nx + 2*nx*b/bands, y - ny + 2*ny*b/bands) for b in range(bands + 1)]
        if prev is not None:
            tx, ty = x - prev[0][0], y - prev[0][1]
            tl = math.hypot(tx, ty) or 1
            s = (tx/tl)*(-math.sin(a)) - (ty/tl)*math.cos(a)        # >0 front face, <0 back face
            face = pal["front"] if s >= 0 else pal["back"]
            edge_on = (1 - abs(s))**1.15                                # 1 when the ribbon is seen edge-on
            for b in range(bands):
                u = 2*(b + 0.5)/bands - 1                               # -1…1 across the nib
                curve = 0.30*u*u - 0.07 + 0.06*u                        # cross-section: rims lit, centre deep
                col = mix(face[0], face[1], edge_on + curve*(0.6 if s >= 0 else 0.4))
                q = [prev[1][b], prev[1][b+1], edge[b+1], edge[b]]
                d = "M" + " L".join(f"{px:.2f} {py:.2f}" for px, py in q) + " Z"
                o.append(f'<path d="{d}" fill="{col}" stroke="{col}" stroke-width="1.1" stroke-linejoin="round"/>')
        prev = ((x, y), edge)
    return "".join(o)


def wordmark(pal):
    # م — looped head sitting on the sweep, tail dropping through it
    meem = ribbon([(640, 584), (604, 590), (566, 580), (528, 538), (540, 482), (592, 462), (638, 494),
                   (630, 552), (584, 586), (532, 614), (500, 664), (486, 736)],
                  58, [(0, 62), (1, 66)], [(0, 0.6), (0.08, 1), (0.82, 1), (1, 0.04)], pal)
    # ا — curls in from the left, then drops as a thick blade
    alef = ribbon([(690, 236), (726, 196), (770, 206), (774, 280), (766, 400), (758, 510), (754, 584)],
                  66, [(0, 16), (1, 6)], [(0, 0.85), (0.1, 1), (0.85, 1), (1, 0.4)], pal)
    # ر — flag-like head, falls, folds, then sweeps left under the word and rises to a blade point
    reh = ribbon([(992, 300), (1050, 282), (1092, 322), (1088, 440), (1046, 532), (952, 600),
                  (806, 640), (646, 654), (506, 640), (392, 600), (326, 552)],
                 88, [(0, 70), (0.55, 68), (1, 76)], [(0, 0.9), (0.06, 1), (0.72, 1), (1, 0.02)], pal, per=50)
    # fatha — one short folded flick
    fatha = ribbon([(880, 262), (926, 230), (978, 214), (1012, 186)], 46, [(0, 70), (1, 40)],
                   [(0, 0.9), (0.2, 1), (1, 0.08)], pal)
    return f'<g transform="translate(80 24)">{alef + meem + reh + fatha}</g>'


THEMES = {
    "khaki": dict(bg="#B5B28C", ink="#1C1E1A", sub="#2E3127", line="#2E3127",
                  front=("#0D0E0C", "#6E7068"), back=("#34362F", "#B4B6AA")),
    "navy": dict(bg="#101C2C", ink="#D9A866", sub="#9AA3AE", line="#4A5666",
                 front=("#6B4319", "#E8B878"), back=("#A97A45", "#F6DDB4")),
}


def poster(theme):
    t = THEMES[theme]
    W, H = 1600, 1000
    b = [f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>', wordmark(t),
         f'<text x="646" y="816" font-family="Cinzel" font-weight="700" font-size="46" fill="{t["ink"]}" letter-spacing="9">RAM</text>',
         f'<text x="648" y="848" font-family="Barlow Condensed" font-weight="600" font-size="17" fill="{t["sub"]}" letter-spacing="4.5">MILITARY &amp; SECURITY AFFAIRS</text>',
         f'<line x1="70" y1="905" x2="{W-70}" y2="905" stroke="{t["line"]}" stroke-width="1.5"/>',
         f'<text x="70" y="880" font-family="Barlow Condensed" font-weight="700" font-size="20" fill="{t["sub"]}" letter-spacing="3">RAM</text>',
         f'<text x="70" y="940" font-family="Barlow Condensed" font-weight="700" font-size="20" fill="{t["sub"]}" letter-spacing="3">2026</text>',
         f'<text x="{W-70}" y="880" font-family="Tajawal" font-weight="800" font-size="24" fill="{t["sub"]}" text-anchor="start" direction="rtl">رَام</text>',
         f'<text x="{W-70}" y="940" font-family="Tajawal" font-weight="500" font-size="20" fill="{t["sub"]}" text-anchor="start" direction="rtl">للشؤون العسكرية والأمنية</text>']
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(b)}</svg>'


if __name__ == "__main__":
    for th in THEMES:
        open(os.path.join(OUT, f"ribbon-{th}.svg"), "w").write(poster(th))
    print("ok")
