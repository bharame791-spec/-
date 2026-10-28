"""RAM | رام — logofolio: 12 custom wordmark studies.

Every wordmark is drawn in its own local frame (baseline y=0, م on the left,
ا in the middle, ر on the right). FG / BG are tokens swapped per board theme.
The board script fits each wordmark into its cell with getBBox().
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out3")
os.makedirs(OUT, exist_ok=True)


def poly(*pts):
    return "M" + " L".join(f"{x} {y}" for x, y in pts) + " Z"


def f(d, extra=""):
    return f'<path d="{d}" fill="FG" {extra}/>'


def bgp(d, extra=""):
    return f'<path d="{d}" fill="BG" {extra}/>'


def s(d, w, color="FG", cap="butt"):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-linecap="{cap}" stroke-linejoin="round"/>'


def txt(x, y, t, size, fam="Barlow Condensed", weight=700, anchor="start", ls=0, color="FG", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{weight}" font-size="{size}" '
            f'fill="{color}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{t}</text>')


# 01 · STENCIL — military crate lettering, every letter bridged
def stencil():
    o = [f("M-50 -170 H130 V0 H10 V110 H-50 Z M10 -110 V-60 H70 V-110 Z", 'fill-rule="evenodd"'),
         f(poly((170, -300), (230, -330), (230, 0), (170, 0))),
         f("M300 -170 H360 V50 L310 110 H220 V50 H300 Z"),
         f(poly((282, -205), (372, -250), (372, -228), (282, -183)))]
    for x, y, w, h in ((34, -176, 13, 72), (34, -66, 13, 72), (164, -150, 72, 13), (294, -58, 72, 13), (262, 44, 13, 72)):
        o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="BG"/>')
    return "".join(o)


# 02 · SAIF — the reh is a drawn Arab sword
def saif():
    return "".join([
        f("M 428 -170 C 436 -10 350 110 130 162 C 316 96 388 -10 392 -170 Z"),          # blade
        f("M 400 -236 H 420 V -176 H 400 Z"),                                              # grip
        f(poly((382, -176), (410, -186), (438, -176), (410, -168))),                       # guard
        '<circle cx="410" cy="-246" r="13" fill="FG"/>',                                   # pommel
        f(poly((238, -318), (292, -340), (281, 0), (255, 6))),                             # alef, nib-cut
        '<circle cx="100" cy="-50" r="54" fill="FG"/><circle cx="104" cy="-54" r="17" fill="BG"/>',
        f("M 58 -44 C 54 50 44 112 34 172 L 18 172 C 24 112 24 50 16 -44 Z"),             # meem tail
        f(poly((316, -196), (362, -224), (366, -214), (320, -186))),                       # fatha
    ])


# 03 · TACTICAL — the reh is a maneuver arrow from an operations map
def tactical():
    band = "M 400 -182 V -30 C 400 70 350 110 270 110 H 250"
    inner = "M 400 -168 V -30 C 400 70 350 110 270 110 H 262"
    return "".join([
        '<rect x="200" y="-300" width="56" height="300" fill="FG"/>',
        '<circle cx="60" cy="-62" r="62" fill="FG"/><circle cx="60" cy="-62" r="19" fill="BG"/>',
        '<rect x="-2" y="-62" width="56" height="212" fill="FG"/>',
        s(band, 56), f(poly((252, 50), (252, 170), (160, 110))),
        s(inner, 34, "BG"), bgp(poly((262, 72), (262, 148), (196, 110))),
    ])


# 04 · KUFI SEAL — square kufic inside a seal frame
def seal():
    U = 30
    sc = lambda d: d
    o = [f'<g transform="scale({U})">',
         f("M0 0 H13 V13 H0 Z M0.75 0.75 V12.25 H12.25 V0.75 Z", 'fill-rule="evenodd"'),
         f("M2 6 H5 V9 H3 V11 H2 Z M3 7 V8 H4 V7 Z", 'fill-rule="evenodd"'),
         f(poly((6, 2.7), (7, 2), (7, 9), (6, 9))),
         f("M10 6 H11 V11 H8 V10 H10 Z"),
         f(poly((8.3, 4.9), (11, 3.45), (11, 4.2), (8.3, 5.65))),
         '</g>',
         txt(2*U, 4.25*U, "RAM", 2.05*U, ls=4)]
    return "".join(o)


# 05 · RADAR LINES — solid letters sliced by scan lines
def radar():
    o = ['<rect x="210" y="-320" width="80" height="320" fill="FG"/>',
         f("M 380 -180 H 460 V -20 C 460 80 400 130 300 130 H 290 V 50 H 300 C 360 50 380 30 380 -20 Z"),
         '<circle cx="80" cy="-70" r="80" fill="FG"/><rect x="0" y="-70" width="80" height="220" fill="FG"/>']
    for k in range(17):
        y = -330 + k*30 + 20
        o.append(f'<rect x="-10" y="{y}" width="480" height="9" fill="BG"/>')
    return "".join(o)


# 06 · INSIGNIA — embroidered strokes with a single inline running through
def insignia():
    return "".join([
        s("M 250 -310 V 0", 72), s("M 400 -180 V -30 C 400 70 340 115 250 115 H 228", 72),
        '<circle cx="80" cy="-64" r="60" fill="none" stroke="FG" stroke-width="72"/>', s("M 20 -64 V 150", 72),
        s("M 250 -287 V -23", 7, "BG"), s("M 400 -157 V -30 C 400 70 340 115 250 115 H 252", 7, "BG"),
        '<circle cx="80" cy="-64" r="60" fill="none" stroke="BG" stroke-width="7"/>', s("M 20 -64 V 127", 7, "BG"),
    ])


# 07 · HAIRLINE — light monoline naskh with a spaced serif caption
def hairline():
    return "".join([
        s("M 290 -300 V 0", 9, cap="round"), s("M 290 -300 L 268 -287", 9, cap="round"),
        s("M 420 -150 C 430 -40 410 60 330 110 C 300 128 270 135 236 136", 9, cap="round"),
        '<circle cx="140" cy="-36" r="36" fill="none" stroke="FG" stroke-width="9"/>',
        s("M 104 -36 C 100 40 92 110 72 170", 9, cap="round"),
        s("M 384 -214 L 432 -240", 9, cap="round"),
        txt(255, 260, "RAM", 64, "Cinzel", 600, "middle", 26),
    ])


# 08 · HEAVY — ultra-bold, tiny counters, matched Latin underneath
def heavy():
    return "".join([
        '<circle cx="95" cy="-95" r="95" fill="FG"/><circle cx="104" cy="-102" r="24" fill="BG"/>',
        '<rect x="0" y="-95" width="110" height="255" fill="FG"/>',
        f(poly((240, -300), (350, -340), (350, 0), (240, 0))),
        f("M 400 -190 H 510 V -10 C 510 90 450 140 350 140 H 320 V 40 H 350 C 385 40 400 20 400 -10 Z"),
        txt(0, 300, "RAM", 122, "Rubik", 700, "start", 0, extra='textLength="510" lengthAdjust="spacing"'),
    ])


# 09 · FACETED — armour-plate geometry, every cut at 45°
def faceted():
    return "".join([
        f("M50 -160 H130 L170 -120 V-40 L130 0 H70 V120 L10 160 V-120 Z "
          "M82 -100 H98 L110 -88 V-72 L98 -60 H82 L70 -72 V-88 Z", 'fill-rule="evenodd"'),
        f(poly((220, -290), (280, -350), (280, 0), (220, 0))),
        f(poly((350, -170), (410, -230), (410, 25), (295, 140), (210, 140), (350, 0))),
        f(poly((300, -232), (352, -284), (352, -262), (300, -210))),
    ])


# 10 · HORIZON — thick verticals, the reh runs out as a long horizon line
def horizon():
    return "".join([
        f("M 430 -170 L 480 -190 L 480 10 C 480 50 460 64 420 64 L -60 64 L -42 50 L 410 50 C 425 50 430 40 430 10 Z"),
        f(poly((290, -320), (332, -338), (332, 18), (290, 18))),
        '<circle cx="128" cy="-26" r="44" fill="FG"/><circle cx="132" cy="-30" r="12" fill="BG"/>',
        f(poly((84, -26), (108, -26), (108, 120), (84, 144))),
        f(poly((384, -214), (440, -244), (444, -232), (388, -202))),
        txt(480, 112, "RAM", 34, anchor="end", ls=10),
    ])


# 11 · NAME TAPE — letters punched out of a stitched uniform tape
def tape():
    tape = "M -40 -140 H 560 V 60 H -40 Z"
    letters = ('<rect x="230" y="-330" width="56" height="320"/>'
               '<circle cx="90" cy="-50" r="58"/><rect x="32" y="-50" width="56" height="200"/>'
               '<path d="M 430 -110 V -20 C 430 70 380 120 300 132" fill="none" stroke-width="56"/>')
    return "".join([
        '<defs><mask id="tapeCut" maskUnits="userSpaceOnUse" x="-100" y="-400" width="800" height="700">'
        '<rect x="-100" y="-400" width="800" height="700" fill="#fff"/>'
        f'<g fill="#000" stroke="#000">{letters}</g></mask>'
        '<mask id="tapeOut" maskUnits="userSpaceOnUse" x="-100" y="-400" width="800" height="700">'
        '<rect x="-100" y="-400" width="800" height="700" fill="#fff"/>'
        f'<path d="{tape}" fill="#000"/></mask></defs>',
        f'<path d="{tape}" fill="FG" mask="url(#tapeCut)"/>',
        f'<g fill="FG" stroke="FG" mask="url(#tapeOut)">{letters}</g>',
        '<circle cx="94" cy="-54" r="19" fill="FG"/>',
        '<rect x="-28" y="-128" width="576" height="176" fill="none" stroke="BG" stroke-width="3" stroke-dasharray="10 7"/>',
        txt(540, 30, "RAM", 34, anchor="end", ls=4, color="BG"),
    ])


# 12 · TOWER — tall condensed kufi with a vertical Latin line
def tower():
    return "".join([
        '<rect x="150" y="-480" width="36" height="480" fill="FG"/>',
        f("M20 -200 H110 V0 H56 V140 H20 Z M56 -164 V-36 H74 V-164 Z", 'fill-rule="evenodd"'),
        f("M236 -220 H272 V140 H206 V104 H236 Z"),
        f(poly((226, -268), (282, -300), (282, -282), (226, -250))),
        txt(0, 0, "RAM · MILITARY &amp; SECURITY", 26, ls=5, extra='transform="translate(-14 140) rotate(-90)"'),
    ])


LOGOS = [
    ("01", "ستنسل", "STENCIL", stencil),
    ("02", "السيف", "SAIF", saif),
    ("03", "سهم العمليات", "TACTICAL", tactical),
    ("04", "الختم الكوفي", "KUFI SEAL", seal),
    ("05", "خطوط الرادار", "RADAR LINES", radar),
    ("06", "الشارة", "INSIGNIA", insignia),
    ("07", "الخط الرفيع", "HAIRLINE", hairline),
    ("08", "الثقيل", "HEAVY", heavy),
    ("09", "الدرع المضلّع", "FACETED", faceted),
    ("10", "الأفق", "HORIZON", horizon),
    ("11", "شريط الاسم", "NAME TAPE", tape),
    ("12", "البرج", "TOWER", tower),
]

THEMES = {
    "olive": dict(bg="#4E5137", fg="#ECE7D8", sub="#B9B79C", line="#666A4C"),
    "light": dict(bg="#E9E8E4", fg="#121417", sub="#6E6F6A", line="#D3D2CC"),
}


def board(theme):
    t = THEMES[theme]
    W, H, M = 1200, 1720, 60
    cw, ch, top = (W - 2*M) / 3, 330, 300
    b = [f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
         txt(M, 112, "RAM Logofolio", 62, "Rubik", 700, color=t["fg"]),
         txt(M, 156, "12 ARABIC LOGOTYPE STUDIES · رام", 22, "Barlow Condensed", 600, ls=3, color=t["sub"]),
         txt(M, 186, "MILITARY &amp; SECURITY AFFAIRS · 2026", 22, "Barlow Condensed", 600, ls=3, color=t["sub"]),
         txt(W - M, 108, "رَام", 92, "Tajawal", 800, "start", color=t["fg"], extra='direction="rtl"'),
         txt(W - M, 186, "للشؤون العسكرية والأمنية", 30, "Tajawal", 500, "start", color=t["sub"], extra='direction="rtl"'),
         f'<line x1="{M}" y1="230" x2="{W-M}" y2="230" stroke="{t["line"]}" stroke-width="1.5"/>']
    for i, (num, ar, en, fn) in enumerate(LOGOS):
        r, c = divmod(i, 3)
        x0, y0 = M + c*cw, top + r*ch
        body = fn().replace("FG", t["fg"]).replace("BG", t["bg"])
        b.append(f'<g class="logo" data-x="{x0 + cw/2}" data-y="{y0 + 130}" data-w="230" data-h="175">{body}</g>')
        b.append(txt(x0 + cw/2, y0 + 285, f"{num} · {en}", 15, "Barlow Condensed", 700, "middle", 3, t["sub"]))
        b.append(txt(x0 + cw/2, y0 + 308, ar, 17, "Tajawal", 500, "middle", 0, t["sub"], 'direction="rtl"'))
    b.append(f'<line x1="{M}" y1="{H-70}" x2="{W-M}" y2="{H-70}" stroke="{t["line"]}" stroke-width="1.5"/>')
    b.append(txt(W/2, H-34, "رَام · RAM — نقرأ القوة، ونحلل الصراع", 18, "Tajawal", 500, "middle", 0, t["sub"]))
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{"".join(b)}</svg>'


if __name__ == "__main__":
    for th in THEMES:
        open(os.path.join(OUT, f"logofolio-{th}.svg"), "w").write(board(th))
    print("ok")
