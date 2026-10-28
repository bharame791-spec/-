import math, os, random

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

NAVY = "#0F1D30"
NAVY2 = "#172941"
SLATE = "#5E6B7D"
GREY = "#8C96A5"
LGREY = "#D3D8DE"
BG = "#EDEFF2"
COPPER = "#B8743F"
COPPER2 = "#D3925C"
CREAM = "#EEE8DD"

AR_FULL = "للدراسات العسكرية والاستراتيجية"
SLOGAN = "نقرأ القوة، ونحلل الصراع"
EN_FULL = "MILITARY &amp; STRATEGIC STUDIES"


def svg(w, h, body, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'{rect}{body}</svg>')


def T(x, y, s, size, fill, fam="Tajawal", weight=700, anchor="middle", ls=0, extra=""):
    d = ' direction="rtl"' if any('؀' <= c <= 'ۿ' for c in s) else ""
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{weight}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" letter-spacing="{ls}"{d} {extra}>{s}</text>')


def P(pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


# ---------------------------------------------------------------- 1 · Square Kufic (Alsharq)
def kufic_block(fg, accent, box_text_fill, u=50):
    r = lambda x, y, w, h: f'<rect x="{x*u}" y="{y*u}" width="{w*u}" height="{h*u}" fill="{fg}"/>'
    parts = []
    # alef — spear-cut top
    parts.append(f'<path d="{P([(6*u, 1.0*u), (7*u, 0), (7*u, 8*u), (6*u, 8*u)])}" fill="{fg}"/>')
    # meem — square ring + descending tail
    parts.append(f'<path d="M0 {4*u} H{4*u} V{8*u} H{1*u} V{10*u} H0 Z M{1*u} {5*u} V{7*u} H{3*u} V{5*u} Z" fill="{fg}" fill-rule="evenodd"/>')
    # reh — stem + foot
    parts.append(f'<path d="M{9*u} {5*u} H{10*u} V{10*u} H{7.4*u} V{9*u} H{9*u} Z" fill="{fg}"/>')
    # fatha
    parts.append(f'<path d="{P([(8.3*u, 3.55*u), (10*u, 2.6*u), (10*u, 3.4*u), (8.3*u, 4.35*u)])}" fill="{accent}"/>')
    # compass-needle diamond in meem counter
    cx, cy = 2*u, 6*u
    parts.append(f'<path d="{P([(cx, cy-0.72*u), (cx+0.42*u, cy), (cx, cy+0.72*u), (cx-0.42*u, cy)])}" fill="{accent}"/>')
    parts.append(f'<path d="{P([(cx, cy-0.72*u), (cx+0.42*u, cy), (cx-0.42*u, cy)])}" fill="#fff" opacity=".22"/>')
    # latin lockup in the empty top-left field
    parts.append(T(0, 1.95*u, "RAM", 2.55*u, fg, "Barlow Condensed", 700, "start", 10))
    parts.append(T(0.05*u, 2.85*u, "STRATEGIC STUDIES", 0.47*u, accent, "Barlow Condensed", 700, "start", 3.2))
    # box with full name
    parts.append(f'<rect x="0" y="{10.6*u}" width="{10*u}" height="{2.5*u}" fill="{fg}"/>')
    parts.append(T(5*u, 12.1*u, AR_FULL, 0.56*u, box_text_fill, "Tajawal", 800))
    return "".join(parts), 10*u, 13.1*u


def logo1():
    W, H = 1600, 1000
    body = []
    for i, (bg, fg, acc, boxt, sub) in enumerate([(NAVY, CREAM, COPPER2, NAVY, GREY), (BG, NAVY, COPPER, BG, SLATE)]):
        ox = i*800
        body.append(f'<rect x="{ox}" y="0" width="800" height="{H}" fill="{bg}"/>')
        blk, bw, bh = kufic_block(fg, acc, boxt)
        tx, ty = ox + (800-bw)/2, (H-bh)/2 - 40
        body.append(f'<g transform="translate({tx} {ty})">{blk}</g>')
        body.append(T(ox+400, ty+bh+58, SLOGAN, 28, sub, "Tajawal", 500))
    return svg(W, H, "".join(body))


# ---------------------------------------------------------------- 2 · Bold wordmark over topographic compass (Basma)
def topo(cx, cy, rmax, n, color, sw):
    random.seed(7)
    out = []
    ph = [random.uniform(0, 6.28) for _ in range(6)]
    for i in range(1, n+1):
        t = i / n
        base = rmax * t
        pts = []
        # contour “peak” drifts slightly so rings are not concentric
        dx, dy = (1-t)*22, (1-t)*-14
        for k in range(240):
            a = 2*math.pi*k/240
            rr = base*(1 + 0.09*math.sin(2*a+ph[0]+t*1.1) + 0.05*math.sin(3*a+ph[1]-t*1.6)
                         + 0.025*math.sin(5*a+ph[2]+t*2))
            pts.append((cx+dx+rr*math.cos(a), cy+dy+rr*math.sin(a)))
        out.append(f'<path d="{P(pts)}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linejoin="round"/>')
    return "".join(out)


def compass_ring(cx, cy, r, color, major=8, minor=72, w=3, inner_text=False):
    o = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{w}"/>']
    for k in range(minor):
        a = 2*math.pi*k/minor - math.pi/2
        L = 26 if k % (minor//4) == 0 else (16 if k % (minor//major) == 0 else 8)
        x1, y1 = cx+r*math.cos(a), cy+r*math.sin(a)
        x2, y2 = cx+(r-L)*math.cos(a), cy+(r-L)*math.sin(a)
        o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w*0.8 if L<20 else w}"/>')
    return "".join(o)


def logo2():
    W = H = 1200
    b = []
    cx, cy = 600, 520
    # emblem
    b.append(f'<clipPath id="c2"><circle cx="{cx}" cy="{cy}" r="262"/></clipPath>')
    b.append(f'<g clip-path="url(#c2)">{topo(cx, cy, 232, 11, COPPER, 3.4)}</g>')
    b.append(compass_ring(cx, cy, 290, COPPER, w=3.4))
    b.append(f'<path d="{P([(cx, cy-345), (cx+20, cy-300), (cx-20, cy-300)])}" fill="{COPPER}"/>')
    # letters — heavy geometric, separated from the emblem by a background halo
    g = []
    g.append(f'<path d="{P([(553, 338), (633, 300), (633, 660), (553, 660)])}"/>')                 # alef
    g.append(f'<path d="M 784 492 V 640 A 112 112 0 0 1 672 752 H 640" fill="none" stroke-width="82"/>')  # reh (stroke)
    g.append(f'<circle cx="420" cy="584" r="80"/>')                                                   # meem head
    g.append(f'<rect x="340" y="584" width="78" height="226"/>')                                       # meem tail
    g.append(f'<path d="{P([(746, 440), (836, 394), (836, 428), (746, 474)])}"/>')                     # fatha
    halo = "".join(g).replace("<path d", f'<path stroke="{BG}" stroke-width="22" stroke-linejoin="miter" d').replace(
        "<circle", f'<circle stroke="{BG}" stroke-width="22"').replace("<rect", f'<rect stroke="{BG}" stroke-width="22"')
    # reh halo needs a wider stroke
    halo = halo.replace('fill="none" stroke-width="82"', 'fill="none" stroke-width="104"')
    b.append(f'<g fill="{BG}" stroke="{BG}">{halo}</g>')
    b.append(f'<g fill="{NAVY}" stroke="{NAVY}">{"".join(g).replace("<path d", "<path stroke-width=\"0\" d").replace("<circle", "<circle stroke-width=\"0\"").replace("<rect", "<rect stroke-width=\"0\"")}</g>')
    # reh has to be stroked; re-draw it with its stroke
    b.append(f'<path d="M 784 492 V 640 A 112 112 0 0 1 672 752 H 640" fill="none" stroke="{NAVY}" stroke-width="82"/>')
    # meem counter: copper compass needle
    b.append(f'<path d="{P([(420, 548), (440, 584), (420, 620), (400, 584)])}" fill="{COPPER}"/>')
    # type
    b.append(T(600, 925, "رام للدراسات العسكرية والاستراتيجية", 46, NAVY, "Tajawal", 800))
    b.append(T(600, 975, "RAM · " + EN_FULL, 24, SLATE, "Barlow Condensed", 600, ls=6))
    b.append(f'<line x1="470" y1="1018" x2="730" y2="1018" stroke="{COPPER}" stroke-width="2"/>')
    b.append(T(600, 1062, SLOGAN, 30, COPPER, "Tajawal", 500))
    return svg(W, H, "".join(b), BG)


# ---------------------------------------------------------------- 3 · Slanted block letters + compass-needle alef (Qarar)
def logo3():
    W = H = 1200
    BGD = "#161E2B"
    b = []
    cx, cy = 600, 520
    # line-art compass behind (sketch layer)
    b.append(compass_ring(cx, cy, 235, CREAM, major=8, minor=120, w=2.2))
    b.append(f'<circle cx="{cx}" cy="{cy}" r="200" fill="none" stroke="{CREAM}" stroke-width="1.4" stroke-dasharray="2 7" opacity=".7"/>')
    for a in range(0, 360, 45):
        ra = math.radians(a)
        b.append(f'<line x1="{cx+60*math.cos(ra):.1f}" y1="{cy+60*math.sin(ra):.1f}" x2="{cx+190*math.cos(ra):.1f}" y2="{cy+190*math.sin(ra):.1f}" stroke="{CREAM}" stroke-width="1.4" opacity=".55"/>')
    for lab, a in (("N", -90), ("E", 0), ("S", 90), ("W", 180)):
        ra = math.radians(a)
        b.append(T(cx+272*math.cos(ra), cy+272*math.sin(ra)+11, lab, 30, CREAM, "Barlow Condensed", 700))
    # bold copper letters, all cut on the same 14° slant
    s = math.tan(math.radians(14))
    # reh: slanted blade that drops below the baseline
    rx, top, bot, wdt = 868, 440, 745, 92
    b.append(f'<path d="{P([(rx, top), (rx+wdt, top-22), (rx+wdt-(bot-top)*s*1.35, bot), (rx-(bot-top)*s*1.35-40, bot+18)])}" fill="{COPPER2}"/>')
    # meem: block head with a square counter + slanted tail
    hx0, hx1, hy0, hy1 = 268, 448, 478, 640
    b.append(f'<path d="M{hx0} {hy0+18} L{hx1} {hy0-6} L{hx1} {hy1} L{hx0} {hy1} Z M{hx0+58} {hy0+68} L{hx1-58} {hy0+56} L{hx1-58} {hy1-54} L{hx0+58} {hy1-54} Z" fill="{COPPER2}" fill-rule="evenodd"/>')
    b.append(f'<path d="{P([(hx0, 600), (hx0+80, 600), (hx0+80-130*s*1.35, 780), (hx0-130*s*1.35-10, 790)])}" fill="{COPPER2}"/>')
    # fatha — two-tone diamond chip, like the reference dots
    b.append(f'<path d="{P([(905, 330), (955, 300), (1005, 330), (955, 360)])}" fill="{COPPER2}"/>')
    # alef = compass needle (north half solid, south half outlined)
    nt, nb, nw = 248, 792, 46
    b.append(f'<path d="{P([(cx, nt), (cx+nw, cy), (cx-nw, cy)])}" fill="{CREAM}"/>')
    b.append(f'<path d="{P([(cx, nt), (cx+nw, cy), (cx, cy)])}" fill="#000" opacity=".16"/>')
    b.append(f'<path d="{P([(cx+nw, cy), (cx, nb), (cx-nw, cy)])}" fill="{BGD}" stroke="{CREAM}" stroke-width="5" stroke-linejoin="miter"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="15" fill="{BGD}" stroke="{COPPER2}" stroke-width="6"/>')
    # small lockup text, bottom-left like the reference
    g = "".join(b); b = [f'<g transform="translate(0 60)">{g}</g>']
    b.append(T(600, 935, AR_FULL, 44, CREAM, "Tajawal", 700))
    b.append(T(600, 982, EN_FULL, 22, GREY, "Barlow Condensed", 600, ls=6))
    b.append(T(600, 1048, "«" + SLOGAN + "»", 30, COPPER2, "Tajawal", 500))
    return svg(W, H, "".join(b), BGD)


# ---------------------------------------------------------------- 4 · Negative-space badge with compass star (Arabic.Design + Nibra)
def star4(cx, cy, R, r):
    pts = []
    for k in range(8):
        a = -math.pi/2 + k*math.pi/4
        rr = R if k % 2 == 0 else r
        pts.append((cx+rr*math.cos(a), cy+rr*math.sin(a)))
    return P(pts)


def logo4():
    W = H = 1200
    BGW = "#EBE8E3"
    b = []
    x0, y0, x1, y1, rad = 405, 395, 795, 785, 34
    badge = (f"M{x0+rad} {y0} H{x1-130} C{x1-40} {y0+10} {x1} {y0+70} {x1} {y0+170} V{y1-rad} "
             f"Q{x1} {y1} {x1-rad} {y1} H{x0+rad} Q{x0} {y1} {x0} {y1-rad} V{y0+rad} Q{x0} {y0} {x0+rad} {y0} Z")
    # letter shapes (single source, used both as cut-outs and as overflow)
    alef = "M 618 262 L 668 250 L 650 662 L 628 666 Z"
    reh = "M 722 548 L 774 532 C 786 650 720 772 548 856 C 660 764 712 666 722 548 Z"
    meem_head = "M 520 556 m -68 0 a 68 68 0 1 0 136 0 a 68 68 0 1 0 -136 0 Z"
    meem_tail = "M 452 560 L 482 560 L 474 870 L 458 872 Z"
    letters = f'<path d="{alef}"/><path d="{reh}"/><path d="{meem_head}"/><path d="{meem_tail}"/>'
    b.append('<defs>'
             f'<mask id="cut"><rect width="{W}" height="{H}" fill="#fff"/><g fill="#000">{letters}</g></mask>'
             f'<clipPath id="inBadge"><path d="{badge}"/></clipPath>'
             f'<mask id="outBadge"><rect width="{W}" height="{H}" fill="#fff"/><path d="{badge}" fill="#000"/></mask>'
             '</defs>')
    b.append(f'<path d="{badge}" fill="{NAVY}" mask="url(#cut)"/>')
    b.append(f'<g fill="{NAVY}" mask="url(#outBadge)">{letters}</g>')
    # compass star inside the meem head (Nibra)
    b.append(f'<path d="{star4(520, 556, 50, 9)}" fill="{COPPER}" clip-path="url(#inBadge)"/>')
    # fatha floating above, like the hamza in the reference
    b.append(f'<path d="M 712 330 L 790 298 L 794 312 L 716 346 Z" fill="{NAVY}"/>')
    # serif lockup
    b.append(T(600, 985, "RAM", 92, NAVY, "Cinzel", 700, ls=14))
    b.append(T(600, 1037, "STRATEGIC STUDIES", 36, COPPER, "Cinzel", 700, ls=5))
    b.append(T(600, 1095, "رام للدراسات العسكرية والاستراتيجية", 30, SLATE, "Tajawal", 700))
    return svg(W, H, "".join(b), BGW)


# ---------------------------------------------------------------- 5 · Calligraphic blades & spear terminals (Rewaq)
def logo5():
    W = H = 1200
    BGL = "#F3F3F2"
    INK = "#0C1524"
    b = []
    # reh: spear-tipped stem that sweeps into a long blade beneath the whole word
    reh = ("M 862 352 L 914 438 L 896 436 "
           "C 906 548 884 642 800 698 "
           "C 680 776 452 772 250 676 "
           "C 448 724 650 712 742 650 "
           "C 806 606 828 532 826 432 "
           "L 808 434 Z")
    b.append(f'<path d="{reh}" fill="{INK}"/>')
    # alef: spear
    b.append(f'<path d="M 616 286 L 652 360 L 636 358 L 640 634 L 600 646 L 598 358 L 582 360 Z" fill="{INK}"/>')
    # meem: faceted diamond head, cut counter, blade tail
    b.append(f'<path d="M 452 520 L 518 586 L 452 652 L 386 586 Z M 452 566 L 472 586 L 452 606 L 432 586 Z" fill="{INK}" fill-rule="evenodd"/>')
    b.append(f'<path d="M 400 600 L 418 622 C 380 640 352 652 300 652 C 338 640 366 624 400 600 Z" fill="{INK}"/>')
    # fatha — the single copper accent
    b.append(f'<path d="M 694 452 L 786 396 L 790 410 L 702 470 Z" fill="{COPPER}"/>')
    # lockup
    g = "".join(b); b = [f'<g transform="translate(18 -10)">{g}</g>']
    b.append(T(600, 870, "RAM", 76, INK, "Cinzel", 700, ls=16))
    b.append(T(600, 912, EN_FULL, 22, SLATE, "Barlow Condensed", 600, ls=6))
    b.append(f'<line x1="520" y1="942" x2="680" y2="942" stroke="{COPPER}" stroke-width="2"/>')
    b.append(T(600, 995, AR_FULL, 38, INK, "Tajawal", 700))
    b.append(T(600, 1040, SLOGAN, 26, COPPER, "Tajawal", 500))
    return svg(W, H, "".join(b), BGL)


LOGOS = {"01-kufic": logo1, "02-topo-compass": logo2, "03-needle": logo3, "04-badge": logo4, "05-blade": logo5}

if __name__ == "__main__":
    for name, fn in LOGOS.items():
        open(os.path.join(OUT, name + ".svg"), "w").write(fn())
    print("ok")
