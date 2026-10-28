"""RAM | رام — round 5: calligrams. The three letters are composed into one
military / security symbol instead of sitting side by side."""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out5")
os.makedirs(OUT, exist_ok=True)

NAVY = "#13233A"
COPPER = "#B8743F"
SLATE = "#6B7684"
PAPER = "#F6F5F2"
GRID = "#C9CCD1"


def poly(*pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def T(x, y, t, size, fill, fam="Tajawal", weight=700, anchor="middle", ls=0, extra=""):
    rtl = ' direction="rtl"' if any('؀' <= ch <= 'ۿ' for ch in t) else ""
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{weight}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{rtl} {extra}>{t}</text>')


def tapered_arc(cx, cy, R, a0, a1, w0, w1, taper_from=0.55, n=90):
    """Arc band from a0 to a1 (deg, clockwise in SVG) whose width stays w0 then tapers to w1."""
    outer, inner = [], []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t)
        k = 0 if t < taper_from else ((t - taper_from) / (1 - taper_from)) ** 1.3
        w = w0 + (w1 - w0) * k
        outer.append((cx + (R + w/2) * math.cos(a), cy + (R + w/2) * math.sin(a)))
        inner.append((cx + (R - w/2) * math.cos(a), cy + (R - w/2) * math.sin(a)))
    return poly(*(outer + inner[::-1]))


# 1 · الدرع والنصل — ر right wall, م left wall, ا the blade standing in the middle
def shield():
    reh = "M 125 -185 L 175 -212 L 175 0 C 175 140 95 228 8 288 C 72 216 125 130 125 0 Z"
    tail = "M -175 -160 L -175 0 C -175 140 -95 228 -8 288 C -72 216 -125 130 -125 0 L -125 -160 Z"
    blade = poly((0, -340), (25, -236), (14, 150), (0, 210), (-14, 150), (-25, -236))
    return "".join([
        f'<path d="{tail}" fill="{NAVY}"/>', f'<circle cx="-115" cy="-160" r="60" fill="{NAVY}"/>',
        f'<circle cx="-115" cy="-160" r="23" fill="{PAPER}"/>', f'<circle cx="-115" cy="-160" r="10" fill="{COPPER}"/>',
        f'<path d="{reh}" fill="{NAVY}"/>', f'<path d="{blade}" fill="{NAVY}"/>',
        f'<path d="{poly((0, -340), (25, -236), (14, 150), (0, 210))}" fill="#000" opacity=".22"/>',
        f'<path d="{poly((116, -246), (194, -282), (194, -260), (116, -224))}" fill="{COPPER}"/>',
    ])


# 2 · السيفان — ر a scimitar, ا a straight sword, crossed; م the medallion at the crossing
def swords():
    sword = (f'<circle cx="0" cy="-306" r="13" fill="{NAVY}"/>'
             f'<rect x="-8" y="-296" width="16" height="50" fill="{NAVY}"/>'
             f'<rect x="-40" y="-250" width="80" height="13" rx="4" fill="{COPPER}"/>'
             f'<path d="{poly((-16, -237), (16, -237), (16, 196), (0, 250), (-16, 196))}" fill="{NAVY}"/>'
             f'<path d="{poly((0, -237), (16, -237), (16, 196), (0, 250))}" fill="#000" opacity=".22"/>')
    scim = (f'<path d="M 170 -172 C 182 -26 58 146 -222 240 C 2 112 118 -30 128 -164 Z" fill="{NAVY}"/>'
            f'<path d="{poly((122, -186), (184, -160), (178, -148), (116, -174))}" fill="{COPPER}"/>'
            f'<path d="{poly((142, -182), (160, -176), (190, -238), (172, -244))}" fill="{NAVY}"/>'
            f'<circle cx="186" cy="-252" r="13" fill="{NAVY}"/>')
    meem = (f'<circle cx="0" cy="-8" r="80" fill="{PAPER}"/>'
            f'<path d="{poly((-26, 30), (26, 30), (0, 160))}" fill="{PAPER}" stroke="{PAPER}" stroke-width="26"/>'
            f'<circle cx="0" cy="-8" r="64" fill="{NAVY}"/>'
            f'<path d="{poly((-22, 40), (22, 40), (0, 156))}" fill="{NAVY}"/>'
            f'<circle cx="0" cy="-8" r="25" fill="{PAPER}"/><circle cx="0" cy="-8" r="11" fill="{COPPER}"/>')
    return f'<g transform="rotate(-34)">{sword}</g>{scim}{meem}'


# 3 · الهدف — ر is the ring of a target, م the bullseye, ا the arrow striking it
def target():
    o = [f'<path d="{tapered_arc(0, 10, 205, -78, 96, 50, 3)}" fill="{NAVY}"/>',
         f'<circle cx="0" cy="10" r="262" fill="none" stroke="{GRID}" stroke-width="2" stroke-dasharray="3 9"/>',
         f'<circle cx="0" cy="10" r="74" fill="{NAVY}"/>',
         f'<path d="{poly((-74, 12), (-34, 12), (-58, 222), (-86, 214))}" fill="{NAVY}"/>',
         f'<circle cx="0" cy="10" r="30" fill="{PAPER}"/><circle cx="0" cy="10" r="15" fill="{COPPER}"/>',
         # arrow (alef) — shaft, head and copper fletching
         f'<rect x="-12" y="-372" width="24" height="262" fill="{NAVY}"/>',
         f'<path d="{poly((-36, -122), (36, -122), (0, -66))}" fill="{NAVY}"/>',
         f'<path d="{poly((-12, -318), (-44, -356), (-44, -330), (-12, -292))}" fill="{COPPER}"/>',
         f'<path d="{poly((12, -318), (44, -356), (44, -330), (12, -292))}" fill="{COPPER}"/>',
         f'<path d="{poly((-12, -276), (-44, -314), (-44, -288), (-12, -250))}" fill="{COPPER}"/>',
         f'<path d="{poly((12, -276), (44, -314), (44, -288), (12, -250))}" fill="{COPPER}"/>']
    return "".join(o)


# 4 · الصقر — م is the falcon's head (eye + hooked beak), ر the sweeping wing, ا a flight feather
def falcon():
    return "".join([
        f'<path d="M 196 -318 C 250 -118 182 92 -150 178 C 70 56 128 -118 150 -290 Z" fill="{NAVY}"/>',     # ر wing
        f'<path d="{poly((92, -350), (124, -340), (66, -46), (44, -52))}" fill="{NAVY}"/>',                    # ا feather
        f'<path d="{poly((150, -356), (172, -350), (140, -232), (124, -238))}" fill="{COPPER}"/>',             # fatha feather
        f'<circle cx="-62" cy="-40" r="86" fill="{NAVY}"/>',                                                   # م head
        f'<path d="M -132 -80 C -182 -76 -202 -36 -190 18 C -180 -4 -166 -12 -144 -10 C -134 -30 -130 -56 -132 -80 Z" fill="{NAVY}"/>',  # beak / tail
        f'<circle cx="-92" cy="-58" r="21" fill="{PAPER}"/><circle cx="-96" cy="-58" r="10" fill="{COPPER}"/>',  # eye
        f'<path d="{poly((-124, -90), (-60, -78), (-62, -64), (-124, -70))}" fill="{NAVY}"/>',              # fierce brow
        f'<path d="M -84 -34 C -96 -6 -92 20 -72 44 C -78 14 -70 -12 -62 -32 Z" fill="{PAPER}"/>',            # malar stripe
    ])


# 5 · الحصن — square kufi built as a fortress: ا the keep with arrow slits, م the gatehouse, ر the wall
def fortress():
    u = 32
    o = [f'<g transform="scale({u})">',
         # م gatehouse with arched gate + merlons, its tail dropping into the wall
         f'<path d="M0 -5 H5 V0 H0 Z M1.6 -1.2 V-2.7 A 0.9 0.9 0 0 1 3.4 -2.7 V-1.2 Z" fill="{NAVY}" fill-rule="evenodd"/>',
         f'<path d="M1.6 -1.2 V-2.7 A 0.9 0.9 0 0 1 3.4 -2.7 V-1.2 Z" fill="{COPPER}"/>',
         f'<path d="M0 -5.8 H1.2 V-5 H0 Z M1.9 -5.8 H3.1 V-5 H1.9 Z M3.8 -5.8 H5 V-5 H3.8 Z" fill="{NAVY}"/>',
         f'<rect x="0" y="0" width="1.2" height="2.4" fill="{NAVY}"/>',
         # ا keep, crenellated, with two arrow slits
         f'<path d="M6 -9 H6.55 V-8.4 H7.05 V-9 H7.6 V1.2 H6 Z" fill="{NAVY}"/>',
         f'<rect x="6.68" y="-7.1" width="0.24" height="1.5" rx="0.12" fill="{PAPER}"/>',
         f'<rect x="6.68" y="-4.2" width="0.24" height="1.5" rx="0.12" fill="{PAPER}"/>',
         # ر tower + its foot running left as the curtain wall
         f'<path d="M10.4 -5.5 H10.8 V-4.9 H11.2 V-5.5 H11.6 V2.4 H0 V1.2 H10.4 Z" fill="{NAVY}"/>',
         f'<path d="{poly((8.3, -6.5), (10.9, -7.7), (10.9, -6.95), (8.3, -5.75))}" fill="{COPPER}"/>',
         '</g>']
    return "".join(o)


CONCEPTS = [
    ("01", "الدرع والنصل", "SHIELD &amp; BLADE", "الراء والميم جدارا درع، والألف نصلٌ قائم في قلبه", shield),
    ("02", "السيفان", "CROSSED SWORDS", "الراء سيف معقوف، والألف سيف مستقيم، والميم وسام", swords),
    ("03", "الإصابة", "ON TARGET", "الراء حلقة الهدف، والميم مركزه، والألف سهمٌ يصيبه", target),
    ("04", "الصقر", "THE FALCON", "الميم رأس صقر، والراء جناحه، والألف ريشة", falcon),
    ("05", "الحصن", "THE FORTRESS", "الألف برج، والميم بوابة، والراء سور الحصن", fortress),
]


def board():
    W, cols, cw, ch, top = 1500, 3, 500, 640, 230
    rows = 2
    H = top + rows*ch + 110
    b = [f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
         T(W - 70, 112, "رَام", 92, NAVY, weight=800, anchor="start"),
         T(W - 70, 170, "للشؤون العسكرية والأمنية — الحروف تبني الرمز", 28, SLATE, weight=500, anchor="start"),
         T(70, 104, "RAM", 64, NAVY, "Rubik", 700, "start", 4),
         T(70, 146, "CALLIGRAM CONCEPTS · 05", 22, COPPER, "Barlow Condensed", 700, "start", 4)]
    # reference-style grid: hairlines with dots at the joints
    for c in (1, 2):
        b.append(f'<line x1="{c*cw}" y1="{top}" x2="{c*cw}" y2="{top + rows*ch}" stroke="{GRID}" stroke-width="2"/>')
    b.append(f'<line x1="40" y1="{top + ch}" x2="{W-40}" y2="{top + ch}" stroke="{GRID}" stroke-width="2"/>')
    for c in (1, 2):
        b.append(f'<circle cx="{c*cw}" cy="{top + ch}" r="7" fill="{GRID}"/>')
    for i, (num, ar, en, desc, fn) in enumerate(CONCEPTS):
        r, c = divmod(i, cols)
        x0 = W - (c + 1)*cw          # RTL: first concept top-right
        cx, y0 = x0 + cw/2, top + r*ch
        b.append(f'<g class="logo" data-x="{cx}" data-y="{y0 + 215}" data-w="300" data-h="300">{fn()}</g>')
        b.append(T(cx, y0 + 440, "رَام", 46, NAVY, weight=800))
        b.append(T(cx, y0 + 478, "للشؤون العسكرية والأمنية", 21, NAVY, weight=500))
        b.append(T(cx, y0 + 504, "RAM · MILITARY &amp; SECURITY AFFAIRS", 14, SLATE, "Barlow Condensed", 600, ls=3))
        b.append(f'<line x1="{cx-40}" y1="{y0+530}" x2="{cx+40}" y2="{y0+530}" stroke="{COPPER}" stroke-width="2"/>')
        b.append(T(cx, y0 + 566, f"{num} · {ar}", 22, COPPER, weight=800))
        b.append(T(cx, y0 + 598, desc, 17, SLATE, weight=500))
    # sixth cell: palette + intent note
    x0, y0 = 0, top + ch
    cx = x0 + cw/2
    for j, (col, name) in enumerate(((NAVY, "#13233A"), (COPPER, "#B8743F"), (SLATE, "#6B7684"))):
        b.append(f'<rect x="{cx - 150 + j*104}" y="{y0 + 150}" width="88" height="88" rx="8" fill="{col}"/>')
        b.append(T(cx - 106 + j*104, y0 + 266, name, 15, SLATE, "Barlow Condensed", 600, ls=1))
    b.append(T(cx, y0 + 340, "كل شعار هنا رمزٌ واحد", 26, NAVY, weight=800))
    b.append(T(cx, y0 + 378, "مبنيّ من حروف «رام» نفسها:", 22, SLATE, weight=500))
    b.append(T(cx, y0 + 410, "درع · سيف · هدف · صقر · حصن", 22, COPPER, weight=700))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(b)}</svg>'


if __name__ == "__main__":
    open(os.path.join(OUT, "logofolio-calligrams.svg"), "w").write(board())
    print("ok")
