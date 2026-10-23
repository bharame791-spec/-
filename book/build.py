#!/usr/bin/env python3
"""Builds the book «ما زلتُ أختاركِ» from manuscript.txt into print-ready PDFs.

Outputs (in ./output):
  ma-zilt-akhtaruki-print-interior.pdf  A5 interior for the printer (chapters open on recto pages)
  ma-zilt-akhtaruki-cover.pdf           front and back cover, A5
  ma-zilt-akhtaruki-screen.pdf          cover + interior + back cover, for reading on screens

Usage: python3 build.py
"""
import html
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
BUILD = ROOT / "build"

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

# A key line from each chapter, shown on its opening page. Each part must appear verbatim
# in the chapter text; parts are shown on separate lines.
QUOTES = {
    1: ["كان فيكِ شيء يشبهني."],
    2: ["لأن بعض الأشخاص لا يقاس قربهم بعدد الساعات، بل بالمساحة التي يحتلونها في داخلنا."],
    3: ["كنت أريد أن أكون قويًا، لكنني لم أكن أريد أن أضطر إلى أن أكون قويًا أمامكِ أيضًا."],
    4: ["لكن بعض المواقف تترك فينا أثرًا لا يختفي بمجرد أن نتصالح."],
    5: ["لم أكن أحتاج إلى أن تحلّي المشكلة.", "كنت أحتاج إلى أن تكوني معي وأنا أواجهها."],
    6: ["كنت أخاف أن أجد نفسي مضطرًا إلى الاختيار بين بناء مستقبلي وبين إثبات حبي."],
    7: ["أفرح لأنني ما زلت أسمعها منكِ.", "وأتألم لأنني كنت أتمنى أن تأتي قبل أن أطلبها."],
    8: ["حين تصبح الشاشة أمامي أكثر هدوءًا من رأسي، أتمنى لو أنني أستطيع أن أوقف التفكير قليلًا."],
    9: ["هذا ليس تقليلًا من حبكِ.", "بل اعتراف بأنني أنا أيضًا أستحق أن أكون بخير."],
    10: ["أنا لا أريد أن أخسركِ.", "ولا أريد أن أخسر نفسي وأنا أحاول ألّا أخسركِ."],
    11: ["ربما يحتاج الحب، حين تكبر المسؤوليات، إلى أن يتعلم لغة جديدة."],
    12: ["لكنني أعرف أن الصمت لم يكن يومًا الطريقة التي تمنيت أن نحافظ بها على ما بيننا."],
    13: ["الإنسان قد يكون مشغولًا عن الحديث، لكنه ليس بالضرورة مشغولًا عن الحب."],
    14: ["لأن بعض الحكايات لا تنتهي حين نتعب من كتابتها، بل حين نعرف أخيرًا ماذا نريد أن نقول."],
}

# The book's motif: two points on one line, a gold one for Bahaa and a rose one for Shahd.
# The distance between them follows the story, chapter by chapter.
#   reach  : he reaches toward her, the line only half drawn
#   near   : close together
#   broken : the line cracks between them
#   open   : the line runs on past them, unfinished
DISTANCE = {
    1: (0.62, "reach"), 2: (0.10, "near"), 3: (0.18, "near"), 4: (0.50, "broken"),
    5: (0.46, "near"), 6: (0.60, "near"), 7: (0.52, "near"), 8: (0.64, "near"),
    9: (0.54, "near"), 10: (0.38, "near"), 11: (0.32, "near"), 12: (0.26, "near"),
    13: (0.30, "near"), 14: (0.22, "open"),
}

GOLD, ROSE = "#b08a52", "#a14d58"
GOLD_D, ROSE_D = "#d6b47c", "#d9828d"


def esc(s):
    return html.escape(s, quote=True)


def css_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ar(n):
    return str(n).translate(AR_DIGITS)


# ---------------------------------------------------------------- manuscript

def parse(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    book = {
        "title": paras[0].strip("«» "),
        "subtitle": paras[1],
        "blurb": paras[2],
        "dedication": [],
        "chapters": [],
        "khatima": [],
    }
    i = 3
    assert paras[i] == "إهداء", paras[i]
    i += 1
    while paras[i] != "---":
        book["dedication"].append(paras[i])
        i += 1
    i += 1
    chapter_re = re.compile(r"^الفصل (.+?): (.+)$")
    current = None
    while i < len(paras):
        p = paras[i]
        m = chapter_re.match(p)
        if m:
            current = {"ordinal": m.group(1), "title": m.group(2), "paras": []}
            book["chapters"].append(current)
        elif p == "---":
            current = None
        elif p == "خاتمة":
            current = {"paras": book["khatima"]}
        else:
            current["paras"].append(p)
        i += 1
    assert len(book["chapters"]) == 14, len(book["chapters"])
    for n, ch in enumerate(book["chapters"], 1):
        body = " ".join(ch["paras"])
        for part in QUOTES[n]:
            assert part in body, f"quote for chapter {n} not found: {part}"
    return book


# ---------------------------------------------------------------- motif

_svg_id = 0


def motif(gap, state="near", width_mm=70, dark=False, alone=False):
    """Two points on a line; `gap` is their distance as a fraction of the width."""
    global _svg_id
    _svg_id += 1
    sid = f"m{_svg_id}"
    gold, rose = (GOLD_D, ROSE_D) if dark else (GOLD, ROSE)
    W, H, cy = 700, 60, 30
    half = gap * 310
    xb, xs = 350 + half, 350 - half  # his point on the right (where Arabic reading starts), hers on the left
    r = 8
    parts = [
        f'<svg class="motif" viewBox="0 0 {W} {H}" style="width:{width_mm}mm" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">',
        "<defs>",
        f'<linearGradient id="{sid}l" x1="0" x2="1"><stop offset="0" stop-color="{gold}" stop-opacity="0"/><stop offset="1" stop-color="{gold}" stop-opacity=".55"/></linearGradient>',
        f'<linearGradient id="{sid}r" x1="0" x2="1"><stop offset="0" stop-color="{gold}" stop-opacity=".55"/><stop offset="1" stop-color="{gold}" stop-opacity="0"/></linearGradient>',
        f'<radialGradient id="{sid}g"><stop offset="0" stop-color="{rose}" stop-opacity=".45"/><stop offset="1" stop-color="{rose}" stop-opacity="0"/></radialGradient>',
        "</defs>",
    ]
    thin = 'stroke-width="1.4" fill="none"'
    if state == "open" or alone:
        # the line runs on beyond the points, dashed, without an end
        parts.append(f'<line x1="{xb}" y1="{cy}" x2="{W}" y2="{cy}" stroke="url(#{sid}r)" {thin}/>')
        parts.append(f'<line x1="0" y1="{cy}" x2="{xs if not alone else xb}" y2="{cy}" stroke="url(#{sid}l)" {thin} stroke-dasharray="6 9"/>')
    else:
        parts.append(f'<line x1="{xb}" y1="{cy}" x2="{W}" y2="{cy}" stroke="url(#{sid}r)" {thin}/>')
        parts.append(f'<line x1="0" y1="{cy}" x2="{xs}" y2="{cy}" stroke="url(#{sid}l)" {thin}/>')
    strong = f'stroke="{gold}" stroke-width="2.4" fill="none" stroke-linecap="round"'
    if alone:
        pass
    elif state == "reach":
        mid = (xb + xs) / 2
        parts.append(f'<line x1="{xb - r}" y1="{cy}" x2="{mid}" y2="{cy}" {strong}/>')
        parts.append(f'<line x1="{mid}" y1="{cy}" x2="{xs + r}" y2="{cy}" stroke="{gold}" stroke-width="1.6" stroke-dasharray="3 8" stroke-linecap="round" opacity=".8"/>')
    elif state == "broken":
        mid = (xb + xs) / 2
        parts.append(f'<line x1="{xb - r}" y1="{cy}" x2="{mid + 16}" y2="{cy}" {strong}/>')
        parts.append(f'<line x1="{mid - 16}" y1="{cy}" x2="{xs + r}" y2="{cy}" {strong}/>')
        parts.append(f'<polyline points="{mid + 10},{cy - 12} {mid + 2},{cy + 4} {mid - 4},{cy - 6} {mid - 10},{cy + 12}" stroke="{rose}" stroke-width="1.6" fill="none" stroke-linejoin="round"/>')
    else:
        parts.append(f'<line x1="{xb - r}" y1="{cy}" x2="{xs + r}" y2="{cy}" {strong}/>')
    parts.append(f'<circle cx="{xb}" cy="{cy}" r="{r}" fill="{gold}"/>')
    if not alone:
        parts.append(f'<circle cx="{xs}" cy="{cy}" r="{r * 3.2}" fill="url(#{sid}g)"/>')
        parts.append(f'<circle cx="{xs}" cy="{cy}" r="{r}" fill="{rose}"/>')
    parts.append("</svg>")
    return "".join(parts)


def starfield(seed, n, w=148, h=210, top=0.62, color="#f3e9d8"):
    rnd = random.Random(seed)
    dots = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * top) ** 1.0
        rr = rnd.choice([0.18, 0.22, 0.28, 0.35, 0.5])
        op = rnd.uniform(0.12, 0.55)
        dots.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{rr}" fill="{color}" opacity="{op:.2f}"/>')
    return (f'<svg class="stars" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{"".join(dots)}</svg>')


# ---------------------------------------------------------------- styles

FONTS_CSS = """
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Bold.ttf); font-weight: 700; }
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Italic.ttf); font-style: italic; }
@font-face { font-family: 'Aref Ruqaa'; src: url(fonts/ArefRuqaa-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Aref Ruqaa'; src: url(fonts/ArefRuqaa-Bold.ttf); font-weight: 700; }
@font-face { font-family: 'Reem Kufi'; src: url(fonts/ReemKufi-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Reem Kufi'; src: url(fonts/ReemKufi-Medium.ttf); font-weight: 500; }
"""

BASE_CSS = """
:root {
  --night: #161b28; --night-2: #232b3d;
  --paper: #f8f3ea; --ink: #2a2521; --muted: #8b8076; --hair: #d9cfc1;
  --gold: @GOLD; --rose: @ROSE; --gold-d: @GOLD_D; --rose-d: @ROSE_D;
}
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body { font-family: 'Amiri', serif; color: var(--ink); font-size: 11.5pt; line-height: 1.9;
       font-kerning: normal; text-rendering: optimizeLegibility; }

@page { size: 148mm 210mm; margin: 21mm 17mm 23mm 17mm; }
@page :blank { @top-center { content: none; } @bottom-center { content: none; } }
@page sheet { margin: 0; @top-center { content: none; } @bottom-center { content: none; } }

/* full-page designed sheets */
.sheet { page: sheet; width: 148mm; height: 210mm; position: relative; overflow: hidden;
         break-after: page; break-inside: avoid; display: flex; flex-direction: column;
         align-items: center; justify-content: center; text-align: center; }
.sheet.dark { background: var(--night); color: var(--paper); }
.sheet.paper { background: var(--paper); }
.marker { position: absolute; top: 2mm; left: 2mm; font-size: 2pt; color: var(--paper); line-height: 1; }
.dark .marker { color: var(--night); }
.motif { display: block; margin: 0 auto; height: auto; }
.stars { position: absolute; inset: 0; width: 100%; height: 100%; }

/* ---- cover */
.cover { justify-content: flex-start; padding: 0 16mm;
         background: radial-gradient(ellipse 85mm 70mm at 50% 40%, #2b3550 0%, var(--night) 72%); }
.cover .kicker { position: relative; margin-top: 30mm; font-family: 'Reem Kufi'; font-size: 9.5pt;
                 color: var(--gold-d); }
.cover h1 { position: relative; font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 50pt;
            line-height: 1.25; margin: 14mm 0 0; color: #fbf4e8; }
.cover h1 span { display: block; }
.cover h1 .l2 { color: #fbf4e8; margin-top: -2mm; }
.cover .cover-motif { position: relative; margin-top: 13mm; width: 124mm; }
.cover .sub { position: relative; margin-top: 12mm; font-size: 12.5pt; line-height: 1.8;
              color: rgba(248,243,234,.82); max-width: 96mm; }
.cover .foot { position: absolute; bottom: 16mm; left: 0; right: 0; font-family: 'Reem Kufi';
               font-size: 8pt; color: rgba(248,243,234,.45); }

.back { padding: 0 22mm; background: radial-gradient(ellipse 90mm 80mm at 50% 45%, #222a3e 0%, var(--night) 75%); }
.back .blurb { position: relative; font-size: 13.5pt; line-height: 2.05; color: rgba(248,243,234,.9); }
.back .blurb::before { content: "«"; } .back .blurb::after { content: "»"; }
.back .back-motif { position: relative; margin: 14mm auto 0; }
.back .back-title { position: absolute; bottom: 18mm; left: 0; right: 0; font-family: 'Aref Ruqaa';
                    font-size: 15pt; color: var(--gold-d); }

/* ---- front matter */
.half-title h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 24pt; margin: 0 0 8mm; color: var(--ink); }
.title-page { justify-content: flex-start; padding-top: 46mm; }
.title-page .kicker { font-family: 'Reem Kufi'; font-size: 9.5pt; color: var(--gold); }
.title-page h1 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 40pt; line-height: 1.3;
                 margin: 9mm 0 10mm; color: var(--ink); }
.title-page .sub { margin-top: 10mm; font-size: 12.5pt; color: var(--muted); max-width: 92mm; line-height: 1.8; }
.colophon { justify-content: flex-end; padding: 0 24mm 30mm; font-size: 8.5pt; line-height: 2;
            color: var(--muted); }
.colophon .t { font-family: 'Aref Ruqaa'; font-size: 12pt; color: var(--ink); }
.colophon hr { width: 14mm; border: 0; border-top: 0.3mm solid var(--hair); margin: 4mm auto; }

.dedication { padding: 0 24mm; }
.dedication h2, .prelude h2, .toc h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 22pt;
                margin: 0 0 9mm; color: var(--ink); }
.dedication .to { font-family: 'Aref Ruqaa'; font-size: 19pt; color: var(--rose); margin: 0 0 6mm; }
.dedication p { margin: 0 0 6mm; font-size: 12pt; line-height: 2; }
.dedication .who { display: block; margin: 0 auto 2.5mm; width: 2.4mm; height: 2.4mm; border-radius: 50%; }
.dedication .who.her { background: var(--rose); } .dedication .who.him { background: var(--gold); }

.prelude { padding: 0 22mm; }
.prelude p { margin: 0; font-size: 13.5pt; line-height: 2.15; color: var(--ink); }
.prelude p::before { content: "«"; color: var(--rose); } .prelude p::after { content: "»"; color: var(--rose); }
.prelude .motif { margin-top: 12mm; }

.toc { justify-content: flex-start; padding: 26mm 18mm 0; }
.toc h2 { margin-bottom: 8mm; }
.toc ol { list-style: none; margin: 0; padding: 0; width: 100%; }
.toc li { display: flex; align-items: baseline; gap: 2.5mm; padding: 1.15mm 0; font-size: 10.5pt; line-height: 1.55; }
.toc .num { flex: 0 0 9mm; font-family: 'Aref Ruqaa'; font-size: 13pt; color: var(--rose); text-align: right; }
.toc .name { text-align: right; }
.toc .dots { flex: 1; border-bottom: 0.25mm dotted #bfb3a3; transform: translateY(-1.2mm); min-width: 6mm; }
.toc .pg { flex: 0 0 auto; color: var(--muted); font-size: 10pt; }
.toc li.end .num { color: var(--gold); }

/* ---- chapter opener */
.opener { justify-content: flex-start; padding: 0 20mm; }
.opener .ord { margin-top: 30mm; font-family: 'Reem Kufi'; font-size: 9.5pt; color: var(--gold); position: relative; }
.opener .numeral { position: absolute; top: 34mm; left: 0; right: 0; font-family: 'Aref Ruqaa'; font-weight: 700;
                   font-size: 190pt; line-height: 1; color: var(--rose); opacity: .075; }
.opener h2 { position: relative; font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 25pt; line-height: 1.55;
             margin: 21mm 0 12mm; color: var(--ink); min-height: 30mm; display: flex; align-items: center; justify-content: center; }
.opener .motif { position: relative; }
.opener blockquote { position: absolute; bottom: 30mm; left: 22mm; right: 22mm; margin: 0;
                     font-size: 12pt; line-height: 2; color: var(--muted); }
.opener blockquote::before { content: ""; display: block; width: 10mm; margin: 0 auto 5mm;
                             border-top: 0.3mm solid var(--rose); opacity: .6; }
.opener blockquote span { display: block; }

/* ---- chapter text */
.chapter-body { break-before: page; }
.chapter-body .head { text-align: center; margin: 2mm 0 9mm; }
.chapter-body .head .t { font-family: 'Aref Ruqaa'; font-size: 13pt; color: var(--rose); line-height: 1.6; }
.chapter-body .head .r { width: 12mm; margin: 2.5mm auto 0; border-top: 0.3mm solid var(--hair); }
.chapter-body p { margin: 0; text-indent: 1.4em; text-align: justify; widows: 2; orphans: 2; }
.chapter-body p.first { text-indent: 0; }
.chapter-body p.first::first-line { color: var(--rose); }
.chapter-body p.last-words { text-indent: 0; text-align: center; margin-top: 9mm; font-family: 'Aref Ruqaa';
                             font-weight: 700; font-size: 21pt; color: var(--rose); break-before: avoid; }
.chapter-body .end-mark { margin-top: 8mm; break-inside: avoid; break-before: avoid; }

/* ---- epilogue */
.khatima { padding: 0 22mm; background: radial-gradient(ellipse 90mm 90mm at 50% 50%, #222a3e 0%, var(--night) 78%); }
.khatima h2 { position: relative; font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 24pt; margin: 0 0 4mm; color: var(--gold-d); }
.khatima .motif { position: relative; margin-bottom: 10mm; }
.khatima p { position: relative; margin: 0 0 4.5mm; font-size: 12.5pt; line-height: 2.05; color: rgba(248,243,234,.88); }
.khatima p:last-of-type { margin-top: 6mm; font-family: 'Aref Ruqaa'; font-size: 16pt; color: var(--rose-d); }
.fin { justify-content: center; }
"""

PRINT_CSS = """
.sheet.paper { background: #fff; }
@page :left  { margin-left: 15mm; margin-right: 20mm; }
@page :right { margin-left: 20mm; margin-right: 15mm; }
"""

SCREEN_CSS = """
@page { background: #f8f3ea; }
html { background: var(--paper); }
"""


def page_css(book):
    """Running heads: book title on right-hand pages, chapter title on left-hand pages."""
    head = ("font-family: 'Reem Kufi'; font-size: 7.5pt; color: #9a8f84; "
            "vertical-align: bottom; padding-bottom: 7mm;")
    foot = ("content: counter(page, arabic-indic); font-family: 'Amiri'; font-size: 9.5pt; "
            "color: #8b8076; vertical-align: top; padding-top: 7mm;")
    rules = [
        f"@page :right {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page :left {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page {{ @bottom-center {{ {foot} }} }}",
    ]
    for n, ch in enumerate(book["chapters"], 1):
        rules.append(f"@page ch{n}:left {{ @top-center {{ content: {css_str(ch['title'])}; {head} }} }}")
    return "\n".join(rules)


# ---------------------------------------------------------------- pages

def cover_front(book):
    t = book["title"]
    first, second = t.split(" ", 1)[0] + " " + t.split(" ")[1], t.split(" ", 2)[2]
    return f"""
<div class="sheet dark cover">
  {starfield(7, 150)}
  <div class="kicker">رواية</div>
  <h1><span>{esc(first)}</span><span class="l2">{esc(second)}</span></h1>
  <div class="cover-motif">{motif(0.36, "open", 124, dark=True)}</div>
  <div class="sub">{esc(book['subtitle'])}</div>
</div>"""


def cover_back(book):
    return f"""
<div class="sheet dark back">
  {starfield(11, 90, top=0.35)}
  <p class="blurb">{esc(book['blurb'])}</p>
  <div class="back-motif">{motif(0.22, "open", 46, dark=True)}</div>
  <div class="back-title">{esc(book['title'])}</div>
</div>"""


class Ctx:
    """What a render pass needs to know: whether to stamp page markers, and before which
    recto pages to add a blank page so that they land on a left-hand (odd) page."""

    def __init__(self, mode, toc_pages=None, markers=False, blanks=()):
        self.mode, self.toc_pages, self.markers, self.blanks = mode, toc_pages or {}, markers, set(blanks)

    def recto(self, key):
        """Returns (html before the sheet, html inside it) for a sheet that must open on a recto."""
        before = '<div class="sheet blank"></div>' if key in self.blanks else ""
        inside = f'<span class="marker">QZ{key}QZ</span>' if self.markers else ""
        return before, inside


RECTO_KEYS = ["TI", "DE", "PR", "TO"] + [f"C{n:02d}" for n in range(1, 15)] + ["KH"]


def front_matter(book, ctx):
    t = esc(book["title"])
    out = []
    if ctx.mode == "print":
        out.append(f'<div class="sheet paper half-title"><h2>{t}</h2>{motif(0.16, "near", 30)}</div>')
    b, mk = ctx.recto("TI")
    out.append(f"""{b}
<div class="sheet paper title-page">{mk}
  <div class="kicker">رواية</div>
  <h1>{t}</h1>
  {motif(0.36, "open", 64)}
  <div class="sub">{esc(book['subtitle'])}</div>
</div>""")
    out.append(f"""
<div class="sheet paper colophon">
  <div class="t">{t}</div>
  <div>رواية</div>
  <hr>
  <div>جميع الحقوق محفوظة للمؤلف ©</div>
  <div>الطبعة الأولى، {ar(2026)}</div>
  <hr>
  <div>جُمع النص بخطوط أميري، وعارف رقعة، وريم كوفي</div>
</div>""")
    ded = book["dedication"]
    b, mk = ctx.recto("DE")
    out.append(f"""{b}
<div class="sheet paper dedication">{mk}
  <h2>إهداء</h2>
  <div class="to">{esc(ded[0])}</div>
  <p><span class="who her"></span>{esc(ded[1])}</p>
  <p><span class="who him"></span>{esc(ded[2])}</p>
</div>""")
    b, mk = ctx.recto("PR")
    out.append(f"""{b}
<div class="sheet paper prelude">{mk}
  <p>{esc(book['blurb'])}</p>
  {motif(0.30, "near", 36)}
</div>""")
    items = []
    for n, ch in enumerate(book["chapters"], 1):
        pg = ar(ctx.toc_pages.get(f"C{n:02d}", 0))
        items.append(f'<li><span class="num">{ar(n)}</span><span class="name">{esc(ch["title"])}</span>'
                     f'<span class="dots"></span><span class="pg">{pg}</span></li>')
    items.append(f'<li class="end"><span class="num">•</span><span class="name">خاتمة</span>'
                 f'<span class="dots"></span><span class="pg">{ar(ctx.toc_pages.get("KH", 0))}</span></li>')
    b, mk = ctx.recto("TO")
    out.append(f"""{b}
<div class="sheet paper toc">{mk}
  <h2>الفهرس</h2>
  <ol>{''.join(items)}</ol>
</div>""")
    return "\n".join(out)


def chapter(n, ch, ctx):
    gap, state = DISTANCE[n]
    quote = "".join(f"<span>{esc(q)}</span>" for q in QUOTES[n])
    b, mk = ctx.recto(f"C{n:02d}")
    paras = []
    last = len(ch["paras"]) - 1
    for i, p in enumerate(ch["paras"]):
        cls = "first" if i == 0 else ""
        if n == 14 and i == last:
            cls = "last-words"
        paras.append(f'<p class="{cls}">{esc(p)}</p>' if cls else f"<p>{esc(p)}</p>")
    end_state = "open" if n == 14 else state
    return f"""
<section class="chapter">{b}
  <div class="sheet paper opener">{mk}
    <div class="numeral">{ar(n)}</div>
    <div class="ord">الفصل {esc(ch['ordinal'])}</div>
    <h2>{esc(ch['title'])}</h2>
    {motif(gap, state, 72)}
    <blockquote>{quote}</blockquote>
  </div>
  <div class="chapter-body" style="page: ch{n}">
    <div class="head"><div class="t">{esc(ch['title'])}</div><div class="r"></div></div>
    {''.join(paras)}
    <div class="end-mark">{motif(gap, end_state, 36 if n != 14 else 48)}</div>
  </div>
</section>"""


def khatima(book, ctx):
    b, mk = ctx.recto("KH")
    paras = "".join(f"<p>{esc(p)}</p>" for p in book["khatima"])
    return f"""{b}
<div class="sheet dark khatima">{mk}
  {starfield(23, 60, top=0.3)}
  <h2>خاتمة</h2>
  {motif(0.0, "open", 40, dark=True, alone=True)}
  {paras}
</div>"""


def document(book, part, ctx):
    css = FONTS_CSS + (BASE_CSS.replace("@GOLD_D", GOLD_D).replace("@ROSE_D", ROSE_D)
                       .replace("@GOLD", GOLD).replace("@ROSE", ROSE))
    css += PRINT_CSS if ctx.mode == "print" else SCREEN_CSS
    body = []
    if part == "cover":
        body.append(cover_front(book))
        body.append(cover_back(book))
    else:
        css += "\n" + page_css(book)
        body.append(front_matter(book, ctx))
        for n, ch in enumerate(book["chapters"], 1):
            body.append(chapter(n, ch, ctx))
        body.append(khatima(book, ctx))
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>{esc(book['title'])}</title>
<style>{css}</style></head>
<body>{''.join(body)}</body>
</html>"""


# ---------------------------------------------------------------- build

def render(html_text, name):
    src = ROOT / f"_{name}.html"  # next to fonts/ so relative font URLs resolve
    src.write_text(html_text, encoding="utf-8")
    pdf = BUILD / f"{name}.pdf"
    subprocess.run(["node", str(ROOT / "render.js"), str(src), str(pdf)], check=True)
    (BUILD / f"{name}.html").write_text(html_text, encoding="utf-8")
    src.unlink()
    return pdf


def page_count(pdf):
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, check=True).stdout
    return int(re.search(r"Pages:\s+(\d+)", info).group(1))


def find_markers(pdf):
    pages = {}
    for i in range(1, page_count(pdf) + 1):
        txt = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), str(pdf), "-"],
                             capture_output=True, text=True, check=True).stdout
        for m in re.finditer(r"QZ(\w\w\w?)QZ", txt):
            pages[m.group(1)] = i
    missing = set(RECTO_KEYS) - set(pages)
    if missing:
        sys.exit(f"could not locate pages for: {sorted(missing)}")
    return pages


def build_interior(book, mode):
    """Locate every sheet that must open a spread, add blank pages where needed (print only),
    then fill the table of contents with the final page numbers."""
    pages = find_markers(render(document(book, "interior", Ctx(mode, markers=True)), f"{mode}-probe"))
    blanks = []
    if mode == "print":
        # Every recto sheet starts a fresh page, so a blank page only shifts what follows.
        shift = 0
        for key in RECTO_KEYS:
            if (pages[key] + shift) % 2 == 0:
                blanks.append(key)
                shift += 1
    probe = render(document(book, "interior", Ctx(mode, markers=True, blanks=blanks)), f"{mode}-probe2")
    pages = find_markers(probe)
    if mode == "print":
        wrong = [k for k in RECTO_KEYS if pages[k] % 2 == 0]
        if wrong:
            sys.exit(f"still on a verso page: {wrong}")
    pdf = render(document(book, "interior", Ctx(mode, pages, blanks=blanks)), f"{mode}-interior")
    if page_count(pdf) != page_count(probe):
        sys.exit("pagination changed between passes")
    return pdf, pages


def main():
    OUT.mkdir(exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    book = parse((ROOT / "manuscript.txt").read_text(encoding="utf-8"))

    print_pdf, print_pages = build_interior(book, "print")
    cover_pdf = render(document(book, "cover", Ctx("print")), "cover")
    screen_interior, _ = build_interior(book, "screen")
    
    names = {
        "interior": OUT / "ma-zilt-akhtaruki-print-interior.pdf",
        "cover": OUT / "ma-zilt-akhtaruki-cover.pdf",
        "screen": OUT / "ma-zilt-akhtaruki-screen.pdf",
    }
    names["interior"].write_bytes(print_pdf.read_bytes())
    names["cover"].write_bytes(cover_pdf.read_bytes())
    # screen edition: front cover, interior, back cover
    tmp_front, tmp_back = BUILD / "front.pdf", BUILD / "back.pdf"
    subprocess.run(["pdfseparate", "-f", "1", "-l", "1", str(cover_pdf), str(tmp_front)], check=True)
    subprocess.run(["pdfseparate", "-f", "2", "-l", "2", str(cover_pdf), str(tmp_back)], check=True)
    subprocess.run(["pdfunite", str(tmp_front), str(screen_interior), str(tmp_back), str(names["screen"])], check=True)

    for k, p in names.items():
        print(f"{k:9s} {page_count(p):3d} pages  {p.relative_to(ROOT)}")
    print("chapter pages (print):", {k: v for k, v in sorted(print_pages.items())})


if __name__ == "__main__":
    main()
