import math, os
from gen import svg, T, P, NAVY, NAVY2, SLATE, GREY, BG, COPPER, COPPER2, CREAM

OUT = os.path.join(os.path.dirname(__file__), "out2")
os.makedirs(OUT, exist_ok=True)

AR = "رَام للشؤون العسكرية والأمنية"
AR_SUB = "للشؤون العسكرية والأمنية"
EN = "MILITARY &amp; SECURITY AFFAIRS"
DEEP = "#0A1422"


# ------------------------------------------------------------ concept A · «الرامي» — marksman / reticle
def marksman(fg, acc, bg, sight=True):
    """Wordmark in a local frame: baseline y=0, x ≈ -260…520."""
    W = 44
    meem = ("M 100 -100 A 100 100 0 1 1 -100 -100 A 100 100 0 1 1 100 -100 Z "
            "M 56 -100 A 56 56 0 1 0 -56 -100 A 56 56 0 1 0 56 -100 Z")
    meem_tail = "M -100 -100 H -56 V 160 H -100 Z"
    alef = P([(150, 0), (150, -320), (172, -364), (194, -320), (194, 0)])
    reh = "M 400 -205 V -60 A 140 140 0 0 1 260 80 H 250"
    fatha = P([(318, -262), (440, -318), (440, -292), (318, -236)])
    o = []
    if sight:  # line of sight running through the reticle, broken by every letter
        o.append(f'<line x1="-262" y1="-100" x2="522" y2="-100" stroke="{acc}" stroke-width="3.5"/>')
        for x in (-262, 522):
            o.append(f'<line x1="{x}" y1="-112" x2="{x}" y2="-88" stroke="{acc}" stroke-width="3.5"/>')
        for x in (-200, -160, 470):
            o.append(f'<circle cx="{x}" cy="-100" r="5" fill="{acc}"/>')
        halo = 16
        o.append(f'<g fill="{bg}" stroke="{bg}" stroke-width="{2*halo}" stroke-linejoin="miter">'
                 f'<circle cx="0" cy="-100" r="100" fill="none" stroke-width="{44+2*halo}"/>'
                 f'<path d="{meem_tail}"/><path d="{alef}"/></g>')
        o.append(f'<path d="{reh}" fill="none" stroke="{bg}" stroke-width="{W+2*halo}"/>')
        # restore the sight line inside the meem counter
        o.append(f'<line x1="-56" y1="-100" x2="56" y2="-100" stroke="{acc}" stroke-width="3.5"/>')
    o.append(f'<path d="{meem}" fill="{fg}" fill-rule="evenodd"/><path d="{meem_tail}" fill="{fg}"/>')
    o.append(f'<path d="{alef}" fill="{fg}"/>')
    o.append(f'<path d="{reh}" fill="none" stroke="{fg}" stroke-width="{W}"/>')
    o.append(f'<path d="{fatha}" fill="{acc}"/>')
    # reticle inside the meem
    for a in (90, 270):
        ra = math.radians(a)
        o.append(f'<line x1="{56*math.cos(ra):.1f}" y1="{-100+56*math.sin(ra):.1f}" x2="{22*math.cos(ra):.1f}" '
                 f'y2="{-100+22*math.sin(ra):.1f}" stroke="{acc}" stroke-width="5"/>')
    if not sight:
        for a in (0, 180):
            ra = math.radians(a)
            o.append(f'<line x1="{56*math.cos(ra):.1f}" y1="-100" x2="{22*math.cos(ra):.1f}" y2="-100" stroke="{acc}" stroke-width="5"/>')
    o.append(f'<circle cx="0" cy="-100" r="10" fill="{acc}"/>')
    return "".join(o)


def marksman_icon(fg, acc, bg):
    o = [f'<circle cx="0" cy="0" r="100" fill="none" stroke="{fg}" stroke-width="44"/>']
    for a in range(0, 360, 90):
        ra = math.radians(a)
        o.append(f'<line x1="{56*math.cos(ra):.1f}" y1="{56*math.sin(ra):.1f}" x2="{20*math.cos(ra):.1f}" y2="{20*math.sin(ra):.1f}" stroke="{acc}" stroke-width="6"/>')
    for a in range(0, 360, 90):  # notches through the ring
        ra = math.radians(a)
        o.append(f'<line x1="{118*math.cos(ra):.1f}" y1="{118*math.sin(ra):.1f}" x2="{138*math.cos(ra):.1f}" y2="{138*math.sin(ra):.1f}" stroke="{acc}" stroke-width="6"/>')
    o.append(f'<circle r="11" fill="{acc}"/>')
    return "".join(o)


# ------------------------------------------------------------ concept B · «الدرع والنصل» — shield & blade
def shield(fg, acc, bg):
    """Emblem in a local frame centred on x=0, y ≈ -335…290."""
    reh = "M 125 -185 L 175 -212 L 175 0 C 175 140 95 228 8 288 C 72 216 125 130 125 0 Z"
    tail = "M -175 -160 L -175 0 C -175 140 -95 228 -8 288 C -72 216 -125 130 -125 0 L -125 -160 Z"
    blade = P([(0, -340), (25, -236), (14, 150), (0, 210), (-14, 150), (-25, -236)])
    o = [f'<path d="{tail}" fill="{fg}"/>',
         f'<circle cx="-115" cy="-160" r="60" fill="{fg}"/>',
         f'<circle cx="-115" cy="-160" r="23" fill="{bg}"/>',
         f'<circle cx="-115" cy="-160" r="10" fill="{acc}"/>',
         f'<path d="{reh}" fill="{fg}"/>',
         f'<path d="{blade}" fill="{fg}"/>',
         f'<path d="{P([(0, -340), (25, -236), (14, 150), (0, 210)])}" fill="#000" opacity=".2"/>',  # ridge
         f'<path d="{P([(116, -246), (194, -282), (194, -260), (116, -224)])}" fill="{acc}"/>']  # fatha
    return "".join(o)


# ------------------------------------------------------------ presentation board
def board(num, title, idea, primary, inverse, icon, icon_scale):
    W, H = 1600, 1120
    b = [f'<rect width="{W}" height="{H}" fill="{DEEP}"/>',
         f'<rect width="960" height="900" fill="{NAVY}"/>', primary,
         f'<rect x="960" width="640" height="450" fill="{BG}"/>', inverse,
         f'<rect x="960" y="450" width="320" height="450" fill="{COPPER}"/>',
         f'<rect x="1280" y="450" width="320" height="450" fill="{NAVY2}"/>']
    # app icon on copper
    b.append(f'<rect x="1040" y="595" width="160" height="160" rx="36" fill="{NAVY}"/>')
    b.append(f'<g transform="translate(1120 675) scale({icon_scale})">{icon(CREAM, COPPER2, NAVY)}</g>')
    b.append(T(1120, 830, "APP ICON", 16, NAVY, "Barlow Condensed", 700, ls=4))
    # scale test
    x = 1440
    for i, (s, y) in enumerate(((96, 560), (56, 700), (32, 792))):
        b.append(f'<rect x="{x-s/2}" y="{y}" width="{s}" height="{s}" rx="{s*.22}" fill="{CREAM}"/>')
        b.append(f'<g transform="translate({x} {y+s/2}) scale({icon_scale*s/160})">{icon(NAVY, COPPER, CREAM)}</g>')
    b.append(T(1440, 864, "96 · 56 · 32 PX", 16, GREY, "Barlow Condensed", 700, ls=4))
    # concept strip (RTL: right-aligned text uses anchor=start)
    b.append(T(1530, 985, num, 64, COPPER2, "Barlow Condensed", 700, "end"))
    b.append(T(1440, 975, title, 40, CREAM, "Tajawal", 800, "start"))
    for i, line in enumerate(idea):
        b.append(T(1440, 1022 + i*38, line, 24, "#C9CED6", "Tajawal", 500, "start"))
    b.append(T(70, 1060, "RAM — LOGO CONCEPT", 18, GREY, "Barlow Condensed", 700, "start", 5))
    return svg(W, H, "".join(b))


def name_block(cx, y, fg, sub, s=1.0, rule=COPPER2):
    return (T(cx, y, AR, 46*s, fg, "Tajawal", 800) +
            f'<line x1="{cx-150*s}" y1="{y+30*s}" x2="{cx+150*s}" y2="{y+30*s}" stroke="{rule}" stroke-width="{2*s}"/>' +
            T(cx, y+72*s, "RAM  |  " + EN, 24*s, sub, "Barlow Condensed", 600, ls=6*s))


def conceptA():
    prim = (f'<g transform="translate({480-130*1.05} {470}) scale(1.05)">{marksman(CREAM, COPPER2, NAVY)}</g>'
            + name_block(480, 720, CREAM, GREY))
    inv = (f'<g transform="translate({1280-130*0.5} {255}) scale(0.5)">{marksman(NAVY, COPPER, BG)}</g>'
           + name_block(1280, 360, NAVY, SLATE, 0.62, COPPER))
    idea = ["«رام» من رمى: الرامي الذي يصيب هدفه. عين الميم صارت شبكة تصويب، وخط النظر النحاسي",
            "يعبر الكلمة كلها، والألف رأس سهم. الرسالة: تحليل دقيق يصيب جوهر الحدث."]
    return board("A", "الرامي — دقّة الإصابة", idea, prim, inv, marksman_icon, 0.48)


def conceptB():
    prim = (f'<g transform="translate(480 395) scale(0.78)">{shield(CREAM, COPPER2, NAVY)}</g>'
            + name_block(480, 720, CREAM, GREY))
    # horizontal lockup: emblem on the right, text reads from it
    inv = (f'<g transform="translate(1470 228) scale(0.42)">{shield(NAVY, COPPER, BG)}</g>'
           + T(1380, 196, "رَام", 92, NAVY, "Tajawal", 800, "start")
           + T(1380, 270, AR_SUB, 30, SLATE, "Tajawal", 700, "start")
           + f'<line x1="1380" y1="296" x2="1060" y2="296" stroke="{COPPER}" stroke-width="2"/>'
           + T(1380, 326, "RAM | " + EN, 15.5, SLATE, "Barlow Condensed", 600, "end", 3.4, 'transform="translate(0 0)"').replace('text-anchor="end"', 'text-anchor="end"'))
    idea = ["الحروف الثلاثة تبني درعاً: الراء جداره الأيمن، والميم جداره الأيسر، والألف نصلٌ قائم في قلبه.",
            "الدرع للأمن، والنصل للشأن العسكري، والكلمة تُقرأ «رام» بوضوح."]
    return board("B", "الدرع والنصل — حماية وحسم", idea, prim, inv, lambda f, a, g: shield(f, a, g), 0.24)


if __name__ == "__main__":
    open(os.path.join(OUT, "A-marksman.svg"), "w").write(conceptA())
    open(os.path.join(OUT, "B-shield.svg"), "w").write(conceptB())
    print("ok")
