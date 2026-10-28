"""RAM | رام — round 7: defence-tech calligrams (cyber, HUD, orbit, signal, network, AI)."""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out7")
os.makedirs(OUT, exist_ok=True)

BG = "#0B1420"
PANEL = "#101C2B"
ICE = "#E8EEF3"
AMBER = "#E39A4C"
GREY = "#6E7B8B"
FAINT = "#2B3B50"


def poly(*pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def T(x, y, t, size, fill, fam="Tajawal", weight=700, anchor="middle", ls=0, extra=""):
    rtl = ' direction="rtl"' if any('؀' <= ch <= 'ۿ' for ch in t) else ""
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{weight}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{rtl} {extra}>{t}</text>')


def line(d, w, c=ICE, cap="butt", extra=""):
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round" {extra}/>'


# ---- shared "tech" letterforms: monoline weight 44, 45° cuts (baseline 0)
def t_meem(fill, counter, cx=0):
    return (f'<circle cx="{cx}" cy="-58" r="58" fill="{fill}"/>'
            f'<path d="{poly((cx-58, -58), (cx-14, -58), (cx-14, 96), (cx-58, 140))}" fill="{fill}"/>'
            f'<circle cx="{cx}" cy="-58" r="18" fill="{counter}"/>')


def t_alef(fill, x=90, top=-282):
    return f'<path d="{poly((x, top+22), (x+44, top), (x+44, 0), (x, 0))}" fill="{fill}"/>'


def t_reh(fill, x=228):
    return f'<path d="{poly((x, -150), (x+44, -172), (x+44, 0), (x-42, 86), (x-104, 86), (x, -18))}" fill="{fill}"/>'


def t_fatha(fill, x=190):
    return f'<path d="{poly((x, -210), (x+72, -246), (x+72, -226), (x, -190))}" fill="{fill}"/>'


# 1 · CYBER CIRCUIT — every letter is a PCB trace ending in solder pads
def pad(x, y, r=15, c=AMBER):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/><circle cx="{x}" cy="{y}" r="{r*0.4:.1f}" fill="{PANEL}"/>'


def circuit():
    o = [line("M 140 -300 H 220 L 250 -330 H 430", 4, FAINT), line("M 170 60 H 120 L 90 90 H -60", 4, FAINT),
         line("M -70 130 H -170", 4, FAINT), line("M -40 -90 H -150 L -180 -120 H -240", 4, FAINT),
         line("M 290 -180 V -230 L 330 -270 H 430", 4, FAINT), line("M 290 -60 H 400 L 430 -30", 4, FAINT)]
    for x, y in ((430, -330), (-60, 90), (-170, 130), (-240, -120), (430, -270), (430, -30)):
        o.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{FAINT}"/>')
    o += [line("M 140 -300 V 0", 18),                                           # ا
          line("M 290 -180 V -20 L 210 60 H 170", 18),                          # ر
          line("M -10 -120 H 50 L 80 -90 V -30 L 50 0 H -10 L -40 -30 V -90 Z", 18),   # م head
          line("M -40 -50 V 100 L -70 130", 18),                                # م tail
          line("M 200 -230 L 262 -262", 18),                                     # fatha
          f'<rect x="12" y="-72" width="24" height="24" fill="{AMBER}"/>']      # die inside the meem
    for x, y in ((140, -300), (140, 0), (290, -180), (170, 60), (-70, 130), (262, -262)):
        o.append(pad(x, y))
    return "".join(o)


# 2 · HUD LOCK — fighter head-up display; the meem is the locked target
def hud():
    o = [t_meem(ICE, PANEL), t_alef(ICE), t_reh(ICE), t_fatha(ICE)]
    # lock ring on the meem
    o.append(f'<circle cx="0" cy="-58" r="92" fill="none" stroke="{AMBER}" stroke-width="5" stroke-dasharray="110 34.5" transform="rotate(-25 0 -58)"/>')
    for a in (0, 90, 180, 270):
        ra = math.radians(a)
        o.append(f'<line x1="{102*math.cos(ra):.1f}" y1="{-58+102*math.sin(ra):.1f}" x2="{124*math.cos(ra):.1f}" y2="{-58+124*math.sin(ra):.1f}" stroke="{AMBER}" stroke-width="5"/>')
    o.append(f'<circle cx="0" cy="-58" r="6" fill="{AMBER}"/>')
    # corner brackets
    x0, y0, x1, y1, L = -150, -330, 380, 190, 46
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        o.append(line(f"M {x} {y+dy*L} V {y} H {x+dx*L}", 6))
    o.append(T(x0 + 64, y0 + 8, "TGT · LOCK", 22, AMBER, "Barlow Condensed", 700, "start", 3))
    o.append(T(x1 - 16, y1 - 18, "RNG 07.26 KM", 20, GREY, "Barlow Condensed", 700, "end", 3))
    o.append(line(f"M {x1-150} {y1-48} H {x1-16}", 2, GREY))
    return "".join(o)


# 3 · ORBIT — a satellite writes the reh as its orbit around a globe-meem
def orbit():
    cx, cy, rx, ry, rot = 120, -40, 310, 112, -12
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))

    def P(th):
        x, y = rx*math.cos(th), ry*math.sin(th)
        return cx + x*cr - y*sr, cy + x*sr + y*cr

    o = []
    # dashed back half of the orbit
    back = [P(math.radians(a)) for a in range(140, 311, 2)]
    o.append(line("M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in back), 3, GREY, extra='stroke-dasharray="6 9"'))
    # reh: tapered front arc
    outer, inner = [], []
    a0, a1 = -48, 140
    for i in range(121):
        t = i/120
        th = math.radians(a0 + (a1 - a0)*t)
        x, y = P(th)
        x2, y2 = P(th + 0.001)
        tx, ty = x2 - x, y2 - y
        tl = math.hypot(tx, ty)
        nx, ny = -ty/tl, tx/tl
        w = 42 if t < 0.45 else 42*(1 - (t - 0.45)/0.55)**1.2 + 2
        outer.append((x + nx*w/2, y + ny*w/2)); inner.append((x - nx*w/2, y - ny*w/2))
    o.append(f'<path d="{poly(*(outer + inner[::-1]))}" fill="{ICE}"/>')
    # satellite leading the stroke
    sx, sy = P(math.radians(-62))
    o.append(f'<g transform="translate({sx:.1f} {sy:.1f}) rotate(32)">'
             f'<rect x="-11" y="-11" width="22" height="22" fill="{AMBER}"/>'
             f'<rect x="-50" y="-7" width="32" height="14" fill="{AMBER}"/><rect x="18" y="-7" width="32" height="14" fill="{AMBER}"/>'
             f'<line x1="-18" y1="0" x2="18" y2="0" stroke="{AMBER}" stroke-width="3"/></g>')
    # alef
    o.append(t_alef(ICE, 108, -290))
    # globe meem
    gx, gy, R = 0, -70, 62
    o.append(f'<path d="{poly((-80, -64), (-36, -64), (-36, 96), (-80, 140))}" fill="{ICE}"/>')
    o.append(f'<circle cx="{gx}" cy="{gy}" r="{R}" fill="{PANEL}" stroke="{ICE}" stroke-width="18"/>')
    o.append(f'<ellipse cx="{gx}" cy="{gy}" rx="24" ry="{R-6}" fill="none" stroke="{ICE}" stroke-width="3.5"/>')
    o.append(f'<line x1="{gx}" y1="{gy-R+6}" x2="{gx}" y2="{gy+R-6}" stroke="{ICE}" stroke-width="3.5"/>')
    for dy, half in ((0, R-6), (-28, 44), (28, 44)):
        o.append(f'<line x1="{gx-half}" y1="{gy+dy}" x2="{gx+half}" y2="{gy+dy}" stroke="{ICE}" stroke-width="3.5"/>')
    o.append(f'<circle cx="{gx+24}" cy="{gy-28}" r="7" fill="{AMBER}"/>')
    return "".join(o)


# 4 · SIGNAL — the alef is an antenna; the reh is its outermost transmitted wave
def arc(cx, cy, r, a0, a1):
    p0 = (cx + r*math.cos(math.radians(a0)), cy + r*math.sin(math.radians(a0)))
    p1 = (cx + r*math.cos(math.radians(a1)), cy + r*math.sin(math.radians(a1)))
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M {p0[0]:.1f} {p0[1]:.1f} A {r} {r} 0 {large} 1 {p1[0]:.1f} {p1[1]:.1f}"


def signal():
    cx, cy = 0, -150
    o = [f'<path d="{poly((-22, -258), (22, -280), (22, 0), (-22, 0))}" fill="{ICE}"/>']
    for r in (72, 124):
        o.append(line(arc(cx, cy, r, -48, 48), 12, AMBER, "round"))
        o.append(line(arc(cx, cy, r, 132, 228), 12, AMBER, "round"))
    # reh = the outer wave, falling and curling under the antenna
    outer, inner = [], []
    for i in range(121):
        t = i/120
        a = math.radians(-62 + 166*t)
        w = 44 if t < 0.55 else 44*(1 - (t - 0.55)/0.45)**1.1 + 3
        outer.append((cx + (190 + w/2)*math.cos(a), cy + (190 + w/2)*math.sin(a)))
        inner.append((cx + (190 - w/2)*math.cos(a), cy + (190 - w/2)*math.sin(a)))
    o.append(f'<path d="{poly(*(outer + inner[::-1]))}" fill="{ICE}"/>')
    # meem on the far left, receiving
    o.append(t_meem(ICE, PANEL, cx=-262))
    o.append(f'<circle cx="-262" cy="-58" r="7" fill="{AMBER}"/>')
    return "".join(o)


# 5 · INTEL NETWORK — letters built as a graph of nodes and links
def network():
    N = dict(h1=(-10, -132), h2=(62, -100), h3=(62, -28), h4=(-10, 0), h5=(-62, -66),
             t1=(-62, 62), t2=(-96, 140), a1=(156, -300), a2=(156, -150), a3=(156, 0),
             r1=(306, -190), r2=(306, -40), r3=(226, 82), r4=(150, 82), f1=(222, -238), f2=(286, -270))
    edges = ["h1 h2", "h2 h3", "h3 h4", "h4 h5", "h5 h1", "h5 t1", "t1 t2", "a1 a2", "a2 a3",
             "r1 r2", "r2 r3", "r3 r4", "f1 f2"]
    links = ["h2 a2", "h3 a3", "a1 r1", "a2 r2", "f2 r1", "h1 a1"]
    o = []
    for e in links:
        (x1, y1), (x2, y2) = N[e.split()[0]], N[e.split()[1]]
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{FAINT}" stroke-width="3" stroke-dasharray="5 7"/>')
    for e in edges:
        (x1, y1), (x2, y2) = N[e.split()[0]], N[e.split()[1]]
        o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{ICE}" stroke-width="14" stroke-linecap="round"/>')
    for k, (x, y) in N.items():
        if k in ("a1", "h3", "r4", "t2"):
            o.append(f'<circle cx="{x}" cy="{y}" r="19" fill="{AMBER}"/><circle cx="{x}" cy="{y}" r="7" fill="{PANEL}"/>')
        else:
            o.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{ICE}"/>')
    return "".join(o)


# 6 · DEFENCE AI — the meem's head is a processor die
def chip():
    o = [t_alef(ICE, 120, -282), t_reh(ICE, 258), t_fatha(ICE, 220)]
    x0, y0, s = -60, -130, 128
    o.append(f'<rect x="{x0}" y="{y0}" width="{s}" height="{s}" rx="12" fill="{ICE}"/>')
    o.append(f'<path d="{poly((x0, y0+s-10), (x0+44, y0+s-10), (x0+44, y0+s+130), (x0, y0+s+170))}" fill="{ICE}"/>')
    o.append(f'<rect x="{x0+40}" y="{y0+40}" width="48" height="48" rx="4" fill="{PANEL}"/>')
    o.append(f'<rect x="{x0+54}" y="{y0+54}" width="20" height="20" fill="{AMBER}"/>')
    for k in range(4):   # pins: top and right edges
        p = y0 + 18 + k*28
        q = x0 + 18 + k*28
        o.append(f'<rect x="{q}" y="{y0-22}" width="10" height="16" fill="{ICE}"/>')
        o.append(f'<rect x="{x0+s+6}" y="{p}" width="16" height="10" fill="{ICE}"/>')
    # data traces running from the chip into the alef
    o.append(line(f"M {x0+s+22} {y0+32} H 104", 3, AMBER))
    o.append(line(f"M {x0+s+22} {y0+88} H 104", 3, AMBER))
    return "".join(o)


# ================================================================== icon + wordmark system (NASAQ-style lockups)
def wordmark(c=ICE):
    """Clean monoline رام used under every icon."""
    return (f'<circle cx="0" cy="-44" r="38" fill="none" stroke="{c}" stroke-width="26"/>'
            + line("M -30 -18 C -44 6 -54 44 -60 96", 26, c)
            + f'<path d="{poly((87, -186), (113, -200), (113, 0), (87, 0))}" fill="{c}"/>'
            + line("M 210 -126 V -14 L 150 46", 26, c))


def i_shield():
    """Shield whose right half dissolves into pixels; the meem is its keyhole."""
    sh = "M -130 -150 H 130 V 0 C 130 90 60 150 0 182 C -60 150 -130 90 -130 0 Z"
    key = ("M 0 -40 m -30 0 a 30 30 0 1 0 60 0 a 30 30 0 1 0 -60 0 Z "
           "M -12 -22 H 12 L 17 70 H -17 Z")
    px = []
    for gx in range(5):
        for gy in range(11):
            x, y = 4 + gx*26, -150 + gy*30
            if x > 70 and (gx + gy) % 2 == 0:
                continue
            px.append(f'<rect x="{x}" y="{y}" width="22" height="26"/>')
    return (f'<defs><clipPath id="shL"><path d="{sh}"/></clipPath>'
            f'<mask id="kh" maskUnits="userSpaceOnUse" x="-200" y="-200" width="400" height="420">'
            f'<rect x="-200" y="-200" width="400" height="420" fill="#fff"/><path d="{key}" fill="#000"/></mask></defs>'
            f'<g mask="url(#kh)" clip-path="url(#shL)">'
            f'<rect x="-140" y="-160" width="140" height="360" fill="{ICE}"/>'
            f'<g fill="{ICE}">{"".join(px)}</g></g>'
            f'<rect x="150" y="-128" width="22" height="22" fill="{AMBER}"/>'
            f'<rect x="168" y="-72" width="16" height="16" fill="{AMBER}"/>'
            f'<rect x="146" y="-24" width="11" height="11" fill="{AMBER}"/>')


def i_radar():
    """Meem as a radar scope: the head is the screen, the tail its mast."""
    R = 104
    o = [f'<path d="{poly((-R, 0), (-R+46, 0), (-R+46, 150), (-R, 196))}" fill="{ICE}"/>',
         f'<circle r="{R}" fill="{ICE}"/>']
    for i in range(36):
        a0, a1 = math.radians(-70 - i*2.2), math.radians(-70 - (i+1)*2.2)
        op = 0.95*(1 - i/36)**1.4
        o.append(f'<path d="M0 0 L {R*math.cos(a0):.1f} {R*math.sin(a0):.1f} L {R*math.cos(a1):.1f} {R*math.sin(a1):.1f} Z" fill="{AMBER}" opacity="{op:.3f}"/>')
    for r in (36, 70):
        o.append(f'<circle r="{r}" fill="none" stroke="{PANEL}" stroke-width="5"/>')
    o.append(f'<line x1="0" y1="0" x2="{R*math.cos(math.radians(-70)):.1f}" y2="{R*math.sin(math.radians(-70)):.1f}" stroke="{PANEL}" stroke-width="6"/>')
    o.append(f'<circle r="12" fill="{PANEL}"/><circle cx="-52" cy="34" r="8" fill="{PANEL}"/>')
    return "".join(o)


def i_hud():
    """Locked-on meem inside head-up-display brackets."""
    o = [t_meem(ICE, PANEL),
         f'<circle cx="0" cy="-58" r="96" fill="none" stroke="{AMBER}" stroke-width="7" stroke-dasharray="118 32.8" transform="rotate(-25 0 -58)"/>',
         f'<circle cx="0" cy="-58" r="7" fill="{AMBER}"/>']
    for a in (0, 90, 180, 270):
        ra = math.radians(a)
        o.append(f'<line x1="{106*math.cos(ra):.1f}" y1="{-58+106*math.sin(ra):.1f}" x2="{128*math.cos(ra):.1f}" y2="{-58+128*math.sin(ra):.1f}" stroke="{AMBER}" stroke-width="7"/>')
    x0, y0, x1, y1, L = -170, -228, 170, 170, 54
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        o.append(line(f"M {x} {y+dy*L} V {y} H {x+dx*L}", 12, ICE))
    return "".join(o)


def i_orbit():
    """Globe-meem circled by an orbit with its satellite."""
    gx, gy, R = 0, -10, 74
    o = [f'<ellipse cx="0" cy="-10" rx="190" ry="62" fill="none" stroke="{ICE}" stroke-width="7" transform="rotate(-18 0 -10)"/>',
         f'<path d="{poly((-R-14, -4), (-R+30, -4), (-R+30, 150), (-R-14, 194))}" fill="{ICE}"/>',
         f'<circle cx="{gx}" cy="{gy}" r="{R}" fill="{PANEL}" stroke="{ICE}" stroke-width="22"/>',
         f'<ellipse cx="{gx}" cy="{gy}" rx="28" ry="{R-8}" fill="none" stroke="{ICE}" stroke-width="5"/>',
         f'<line x1="{gx}" y1="{gy-R+8}" x2="{gx}" y2="{gy+R-8}" stroke="{ICE}" stroke-width="5"/>']
    for dy, half in ((0, R-8), (-32, 52), (32, 52)):
        o.append(f'<line x1="{gx-half}" y1="{gy+dy}" x2="{gx+half}" y2="{gy+dy}" stroke="{ICE}" stroke-width="5"/>')
    # front arc of the orbit crosses in front of the globe
    o.append(f'<path d="M -186 -48 A 190 62 0 0 0 186 -48" fill="none" stroke="{ICE}" stroke-width="7" transform="rotate(-18 0 -10) translate(0 38)"/>')
    a = math.radians(-35)
    sx, sy = 190*math.cos(a), 62*math.sin(a)
    rr = math.radians(-18)
    px, py = sx*math.cos(rr) - sy*math.sin(rr), -10 + sx*math.sin(rr) + sy*math.cos(rr)
    o.append(f'<g transform="translate({px:.1f} {py:.1f}) rotate(-30)">'
             f'<rect x="-14" y="-14" width="28" height="28" fill="{AMBER}"/>'
             f'<rect x="-60" y="-9" width="38" height="18" fill="{AMBER}"/><rect x="22" y="-9" width="38" height="18" fill="{AMBER}"/></g>')
    return "".join(o)


def i_chip():
    """Meem head as a processor die."""
    x0, y0, s = -80, -170, 160
    o = [f'<rect x="{x0}" y="{y0}" width="{s}" height="{s}" rx="16" fill="{ICE}"/>',
         f'<path d="{poly((x0, y0+s-12), (x0+54, y0+s-12), (x0+54, y0+s+120), (x0, y0+s+170))}" fill="{ICE}"/>',
         f'<rect x="{x0+48}" y="{y0+48}" width="64" height="64" rx="6" fill="{PANEL}"/>',
         f'<rect x="{x0+64}" y="{y0+64}" width="32" height="32" fill="{AMBER}"/>']
    for k in range(4):
        q = x0 + 22 + k*36
        o.append(f'<rect x="{q}" y="{y0-30}" width="14" height="22" fill="{ICE}"/>')
        o.append(f'<rect x="{x0+s+8}" y="{y0+22+k*36}" width="22" height="14" fill="{ICE}"/>')
        if k < 3:
            o.append(f'<rect x="{x0-30}" y="{y0+22+k*36}" width="22" height="14" fill="{ICE}"/>')
        if k > 1:
            o.append(f'<rect x="{x0+22+k*36}" y="{y0+s+8}" width="14" height="22" fill="{ICE}"/>')
    return "".join(o)


def i_signal():
    """Alef antenna; the reh is the outermost wave."""
    cx, cy = 0, -150
    o = [f'<path d="{poly((-24, -262), (24, -286), (24, 0), (-24, 0))}" fill="{ICE}"/>',
         line(arc(cx, cy, 196, 132, 228), 14, ICE, "round")]
    for r in (78, 136):
        o.append(line(arc(cx, cy, r, -48, 48), 14, AMBER, "round"))
        o.append(line(arc(cx, cy, r, 132, 228), 14, AMBER, "round"))
    outer, inner = [], []
    for i in range(121):
        t = i/120
        a = math.radians(-60 + 162*t)
        w = 46 if t < 0.55 else 46*(1 - (t - 0.55)/0.45)**1.1 + 3
        outer.append((cx + (196 + w/2)*math.cos(a), cy + (196 + w/2)*math.sin(a)))
        inner.append((cx + (196 - w/2)*math.cos(a), cy + (196 - w/2)*math.sin(a)))
    o.append(f'<path d="{poly(*(outer + inner[::-1]))}" fill="{ICE}"/>')
    return "".join(o)


CONCEPTS = [
    ("01", "الدرع السيبراني", "CYBER SHIELD", "درع رقمي، والميم ثقب مفتاح فيه: أمن المعلومات", i_shield),
    ("02", "الرادار", "RADAR", "رأس الميم شاشة رادار وذيلها الصاري: رصد وإنذار مبكر", i_radar),
    ("03", "قفل الهدف", "HUD LOCK", "واجهة تصويب حديثة: عين الميم هدفٌ مُقفَل عليه", i_hud),
    ("04", "المدار", "ORBIT", "الميم كرة أرضية يدور حولها قمر صناعي: استطلاع فضائي", i_orbit),
    ("05", "الإشارة", "SIGNAL · EW", "الألف هوائي، والراء أبعد موجة: اتصالات وحرب إلكترونية", i_signal),
    ("06", "الذكاء الدفاعي", "DEFENSE AI", "رأس الميم شريحة معالجة: الذكاء الاصطناعي الدفاعي", i_chip),
]


def board():
    W, M, cols, gap, cw, ch, top = 1500, 50, 3, 20, 453, 640, 230
    H = top + 2*ch + gap + 100
    b = [f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         T(W - M, 110, "رَام", 92, ICE, weight=800, anchor="start"),
         T(W - M, 168, "للشؤون العسكرية والأمنية — أيقونة + اسم", 28, GREY, weight=500, anchor="start"),
         T(M, 100, "RAM", 64, ICE, "Rubik", 700, "start", 4),
         T(M, 142, "DEFENSE-TECH IDENTITY · 06", 22, AMBER, "Barlow Condensed", 700, "start", 4)]
    for i, (num, ar, en, desc, fn) in enumerate(CONCEPTS):
        r, c = divmod(i, cols)
        x0 = W - M - (c+1)*cw - c*gap
        y0 = top + r*(ch + gap)
        cx = x0 + cw/2
        b.append(f'<rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" rx="10" fill="{PANEL}"/>')
        b.append(f'<g class="logo" data-x="{cx}" data-y="{y0 + 165}" data-w="190" data-h="180">{fn()}</g>')
        b.append(f'<g class="logo" data-x="{cx}" data-y="{y0 + 325}" data-w="150" data-h="76">{wordmark()}</g>')
        b.append(T(cx, y0 + 410, "RAM", 34, ICE, "Rubik", 700, ls=10))
        b.append(T(cx, y0 + 446, "للشؤون العسكرية والأمنية", 19, AMBER, weight=700))
        b.append(f'<line x1="{x0+30}" y1="{y0+500}" x2="{x0+cw-30}" y2="{y0+500}" stroke="{FAINT}" stroke-width="1.5"/>')
        b.append(T(x0 + cw - 30, y0 + 548, ar, 26, ICE, weight=800, anchor="start"))
        b.append(T(x0 + 30, y0 + 546, f"{num} · {en}", 18, AMBER, "Barlow Condensed", 700, "start", 3))
        b.append(T(x0 + cw - 30, y0 + 592, desc, 17, GREY, weight=500, anchor="start"))
    b.append(T(W/2, H - 40, "رَام · RAM — نقرأ القوة، ونحلل الصراع", 20, GREY, weight=500))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(b)}</svg>'


if __name__ == "__main__":
    open(os.path.join(OUT, "logofolio-tech.svg"), "w").write(board())
    print("ok")
