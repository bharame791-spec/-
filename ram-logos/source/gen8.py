"""RAM | رام — round 8: the word IS the logo. One custom bold wordmark, six ideas built into the letters."""
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out8")
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


# ---------------------------------------------------------------- the base wordmark
# baseline y=0 · م head x 0…160 · ا x 214…278 · ر stem x 340…404
W = 64
REH = "M 372 -172 V -20 A 120 120 0 0 1 252 100 H 206"


def meem_head(fill, counter=True):
    o = f'<rect x="0" y="-124" width="160" height="124" rx="58" fill="{fill}"/>'
    if counter:
        o += f'<rect x="60" y="-74" width="46" height="26" rx="13" fill="{BG}"/>'
    return o


def meem_tail(fill):
    return f'<path d="{poly((0, -62), (64, -62), (52, 150), (-16, 150))}" fill="{fill}"/>'


def alef(fill):
    return f'<path d="{poly((214, -316), (278, -340), (278, 0), (214, 0))}" fill="{fill}"/>'


def reh(fill):
    return (f'<path d="{REH}" fill="none" stroke="{fill}" stroke-width="{W}"/>'
            f'<path d="{poly((340, -160), (404, -184), (404, -150), (340, -150))}" fill="{fill}"/>')


def fatha(fill):
    return f'<path d="{poly((300, -236), (404, -276), (404, -244), (300, -204))}" fill="{fill}"/>'


def base(fill=ICE, acc=AMBER, counter=True):
    return meem_tail(fill) + meem_head(fill, counter) + alef(fill) + reh(fill) + fatha(acc)


# 1 · RADAR — the meem's eye opens into a radar screen
def radar():
    o = [meem_tail(ICE), f'<rect x="-10" y="-150" width="180" height="150" rx="66" fill="{ICE}"/>']
    cx, cy, R = 80, -75, 50
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{BG}"/>')
    for i in range(30):
        a0, a1 = math.radians(-60 - i*3), math.radians(-60 - (i+1)*3)
        op = 0.95*(1 - i/30)**1.3
        o.append(f'<path d="M{cx} {cy} L {cx+R*math.cos(a0):.1f} {cy+R*math.sin(a0):.1f} L {cx+R*math.cos(a1):.1f} {cy+R*math.sin(a1):.1f} Z" fill="{AMBER}" opacity="{op:.3f}"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="28" fill="none" stroke="{FAINT}" stroke-width="3"/>')
    o.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+R*math.cos(math.radians(-60)):.1f}" y2="{cy+R*math.sin(math.radians(-60)):.1f}" stroke="{AMBER}" stroke-width="3"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{ICE}"/><circle cx="{cx-22}" cy="{cy+14}" r="4" fill="{AMBER}"/>')
    o += [alef(ICE), reh(ICE), fatha(AMBER)]
    return "".join(o)


# 2 · CYBER — square-kufi pixels; the reh breaks up into data
def cyber():
    u, g = 40, 4
    cells = []
    cells += [(x, y) for x in range(4) for y in (-3, -2, -1) if not (y == -2 and x in (1, 2))]   # meem head
    cells += [(0, 0), (0, 1)]                                                                    # meem tail
    cells += [(5, y) for y in range(-7, 0)]                                                      # alef
    cells += [(8, y) for y in range(-4, 2)] + [(7, 1), (6, 1)]                                   # reh
    o = [f'<rect x="{x*u+g/2}" y="{y*u+g/2}" width="{u-g}" height="{u-g}" fill="{ICE}"/>' for x, y in cells]
    o.append(f'<rect x="{1.5*u+6}" y="{-2*u+10}" width="{u-12}" height="{u-20}" fill="{AMBER}"/>')      # lit core in the eye
    for x, y, s in ((6.9, -5.5, .5), (7.4, -5.75, .5), (7.9, -6.0, .5)):                            # pixel fatha
        o.append(f'<rect x="{x*u}" y="{y*u}" width="{s*u}" height="{s*u}" fill="{AMBER}"/>')
    for x, y, s, c in ((9.3, -3.0, .7, ICE), (9.3, -1.0, .7, ICE), (10.3, -2.2, .5, ICE), (9.4, 0.4, .55, AMBER),
                       (10.6, -0.4, .4, AMBER), (11.4, -1.6, .3, ICE), (11.2, 0.9, .28, AMBER), (12.0, -0.6, .2, ICE)):
        o.append(f'<rect x="{x*u}" y="{y*u}" width="{s*u}" height="{s*u}" fill="{c}"/>')
    return "".join(o)


# 3 · PRECISION CUT — one laser-straight slice runs through the whole word
def slice_():
    k, c = -0.34, -40           # cut line y = k·x + c
    x0, x1 = -120, 560
    below = poly((x0, k*x0 + c + 6), (x1, k*x1 + c + 6), (x1, 400), (x0, 400))
    above = poly((x0, k*x0 + c - 6), (x1, k*x1 + c - 6), (x1, -500), (x0, -500))
    return "".join([
        f'<defs><clipPath id="cB"><path d="{below}"/></clipPath><clipPath id="cA"><path d="{above}"/></clipPath></defs>',
        f'<g clip-path="url(#cB)">{base()}</g>',
        f'<g clip-path="url(#cA)"><g transform="translate(10 -4)">{base()}</g></g>',
        f'<line x1="{x0}" y1="{k*x0 + c}" x2="{x1}" y2="{k*x1 + c}" stroke="{AMBER}" stroke-width="2.5"/>',
        f'<circle cx="{x1}" cy="{k*x1 + c}" r="6" fill="{AMBER}"/>',
    ])


# 4 · SHIELD — the meem's counter is a shield (security hidden in the letter)
def shield():
    o = [meem_tail(ICE), f'<rect x="-10" y="-150" width="180" height="150" rx="62" fill="{ICE}"/>']
    sx, sy = 80, -108
    o.append(f'<path d="M {sx-30} {sy} H {sx+30} V {sy+30} C {sx+30} {sy+58} {sx+12} {sy+72} {sx} {sy+80} '
             f'C {sx-12} {sy+72} {sx-30} {sy+58} {sx-30} {sy+30} Z" fill="{BG}"/>')
    o.append(f'<path d="M {sx} {sy+10} H {sx+20} V {sy+30} C {sx+20} {sy+50} {sx+8} {sy+60} {sx} {sy+66} Z" fill="{AMBER}"/>')
    o += [alef(ICE), reh(ICE), fatha(AMBER)]
    return "".join(o)


# 5 · SIGNAL — the reh transmits: its curve repeats outward as waves
def signal():
    cx, cy = 252, -20
    o = [base()]
    for r, w, op in ((186, 13, 1), (232, 10, .65), (274, 7, .35)):
        ang = math.radians(48)
        ex, ey = cx + r*math.cos(ang), cy + r*math.sin(ang)
        o.append(f'<path d="M {cx + r} {-150 + (r-120)*0.55:.1f} V {cy} A {r} {r} 0 0 1 {ex:.1f} {ey:.1f}" fill="none" '
                 f'stroke="{AMBER}" stroke-width="{w}" stroke-linecap="round" opacity="{op}"/>')
    return "".join(o)


# 6 · TRACKING — the reh's tail becomes a tracked trajectory that locks onto a target
def tracking():
    o = [base()]
    pts = [(176, 114), (128, 126), (78, 130), (30, 124), (-18, 106), (-58, 74), (-86, 30),
           (-102, -20), (-106, -72), (-98, -124), (-80, -172), (-54, -212)]
    for i, (x, y) in enumerate(pts):
        o.append(f'<circle cx="{x}" cy="{y}" r="{7.5 - i*0.42:.1f}" fill="{ICE if i < 6 else AMBER}"/>')
    tx, ty = -30, -246
    o.append(f'<circle cx="{tx}" cy="{ty}" r="20" fill="none" stroke="{AMBER}" stroke-width="4"/>')
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        o.append(f'<line x1="{tx+dx*26}" y1="{ty+dy*26}" x2="{tx+dx*38}" y2="{ty+dy*38}" stroke="{AMBER}" stroke-width="4"/>')
    o.append(f'<circle cx="{tx}" cy="{ty}" r="5" fill="{AMBER}"/>')
    return "".join(o)


CONCEPTS = [
    ("01", "الرادار", "RADAR", "عين الميم تنفتح على شاشة رادار: رصد وإنذار مبكر", radar),
    ("02", "الشيفرة", "CYBER", "كوفي من بكسلات، والراء تتفكك إلى بيانات: أمن سيبراني", cyber),
    ("03", "القطع الدقيق", "PRECISION CUT", "خط ليزر واحد يشق الكلمة كلها: دقة وحسم", slice_),
    ("04", "الدرع الخفي", "HIDDEN SHIELD", "عين الميم على شكل درع: الأمن مخبّأ داخل الحرف", shield),
    ("05", "البثّ", "SIGNAL", "انحناءة الراء تتكرر كموجات بثّ: اتصالات وحرب إلكترونية", signal),
    ("06", "التتبّع", "TRACKING", "ذيل الراء مسار مُتتبَّع ينتهي بقفل على الهدف", tracking),
]


def board():
    Wd, M, gap, cw, ch, top = 1600, 50, 20, 740, 500, 230
    H = top + 3*ch + 2*gap + 100
    b = [f'<rect width="{Wd}" height="{H}" fill="{BG}"/>',
         T(Wd - M, 110, "رَام", 92, ICE, weight=800, anchor="start"),
         T(Wd - M, 168, "الكلمة هي الشعار — الفكرة داخل الحروف", 28, GREY, weight=500, anchor="start"),
         T(M, 100, "RAM", 64, ICE, "Rubik", 700, "start", 4),
         T(M, 142, "WORDMARK CONCEPTS · 06", 22, AMBER, "Barlow Condensed", 700, "start", 4)]
    for i, (num, ar, en, desc, fn) in enumerate(CONCEPTS):
        r, c = divmod(i, 2)
        x0 = Wd - M - (c+1)*cw - c*gap
        y0 = top + r*(ch + gap)
        cx = x0 + cw/2
        b.append(f'<rect x="{x0}" y="{y0}" width="{cw}" height="{ch}" rx="10" fill="{PANEL}"/>')
        b.append(f'<g class="logo" data-x="{cx}" data-y="{y0 + 190}" data-w="420" data-h="270">{fn()}</g>')
        b.append(T(cx, y0 + 372, "RAM · MILITARY &amp; SECURITY AFFAIRS", 16, GREY, "Barlow Condensed", 700, ls=4))
        b.append(f'<line x1="{x0+34}" y1="{y0+402}" x2="{x0+cw-34}" y2="{y0+402}" stroke="{FAINT}" stroke-width="1.5"/>')
        b.append(T(x0 + cw - 34, y0 + 446, ar, 28, ICE, weight=800, anchor="start"))
        b.append(T(x0 + 34, y0 + 444, f"{num} · {en}", 18, AMBER, "Barlow Condensed", 700, "start", 3))
        b.append(T(x0 + cw - 34, y0 + 480, desc, 18, GREY, weight=500, anchor="start"))
    b.append(T(Wd/2, H - 40, "رَام للشؤون العسكرية والأمنية — نقرأ القوة، ونحلل الصراع", 20, GREY, weight=500))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {Wd} {H}" width="{Wd}" height="{H}">{"".join(b)}</svg>'


if __name__ == "__main__":
    open(os.path.join(OUT, "logofolio-wordmarks.svg"), "w").write(board())
    print("ok")
