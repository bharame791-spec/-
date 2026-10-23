#!/usr/bin/env python3
"""Builds the novel «ما زلتُ أختاركِ» from manuscript.txt into designed, print-ready PDFs,
following the design brief: navy / warm paper / ivory, Alexandria + IBM Plex Sans Arabic + Amiri,
abstract imagery only (windows, light, paper, empty space), and the text as the hero.

Outputs (in ./output):
  ma-zilt-akhtaruki-print-interior.pdf  A5 interior for the printer (chapters open on recto pages)
  ma-zilt-akhtaruki-cover.pdf           front and back cover, A5
  ma-zilt-akhtaruki-screen.pdf          cover + interior + back cover, for reading on screens

The artwork in ./art comes from illustrate.py (run automatically if ./art is missing).
Usage: python3 build.py
"""
import html
import re
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
BUILD = ROOT / "build"
ART = ROOT / "art"

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")

AUTHOR = "بهاء الدين أبو زبيدة"
YEAR = 2026

BACK_BLURB = [
    "لم تبدأ الحكاية بوعدٍ كبير، ولا بلقاءٍ يشبه ما نراه في الروايات.",
    "بدأت بمحادثة على شاشة صغيرة، ثم بشعورٍ لم أجد له اسمًا في البداية. شيئًا فشيئًا، أصبحت هناك إنسانة أريد أن أخبرها بتفاصيل يومي، وأعود إليها حين يثقل العالم على صدري.",
    "لكن الحب لا يعيش خارج الحياة. هناك العمل، والقلق، والأيام التي لا تتسع لكل ما نريد قوله، والكلمات التي نحتاج إلى سماعها أكثر مما نعترف.",
    "هذه ليست حكاية شخصٍ لا يخطئ، ولا حكاية شخصٍ يتحمل الخطأ وحده. إنها محاولة لفهم ما يحدث حين يحب شخصان بعضهما، لكنهما لا ينجحان دائمًا في الوصول إلى بعضهما.",
    "وهي، قبل كل شيء، حكاية ما زال آخرها مفتوحًا.",
]

OPENING_QUOTE = ["بعض الأشخاص لا يصبحون جزءًا من يومنا فقط؛",
                 "بل يصبحون المكان الذي نذهب إليه حين لا نعرف أين نضع كل ما نشعر به."]

# Pages of a single sentence at the turns of the story, placed after the given chapter.
SEPARATORS = {
    2: "ليس كل ما يؤلمنا يمحو ما أحببناه.",
    4: "أحيانًا لا نحتاج إلى حلّ، بل إلى شخصٍ لا يجعلنا نشرح ألمنا كاملًا.",
    6: "لم تكن كل المسافات تُقاس بالمكان.",
    13: "بعض النهايات لا تحدث في لحظة؛ بل تبقى سؤالًا.",
}

CLOSING = [
    "لا أعرف أين ستأخذنا الأيام، ولا إن كنا سنعرف يومًا كيف نصل إلى بعضنا بالطريقة التي نحتاجها.",
    "كل ما أعرفه أنني أحببتكِ بصدق، وأنني ما زلت أحاول أن أفهم كيف نحمي الأشياء التي نحبها من كل ما يثقلها.",
    "أما النهاية...",
    "فلم أكتبها بعد.",
]

# Quote pages facing a chapter's first page. Each must appear verbatim in that chapter.
CHAPTER_QUOTES = {
    2: ("لأن بعض الأشخاص لا يقاس قربهم بعدد الساعات، بل بالمساحة التي يحتلونها في داخلنا.", "large"),
    7: ("كنت أريد الشعور الذي يسبقها.", "small"),      # a nearly empty page
    10: ("وأنا لا أريد أن أمحو كل ذلك لمجرد أنني أتألم الآن.", "large"),
}

# How each chapter opens, mapped from the brief to the manuscript's chapters:
#   screen  a small screen, not Instagram itself      window   a small lit window
#   dark    a dark opening page                       presence one point present, one missing
#   gap     two spaces with a gap, one colour linking  stack    tasks piling up
#   letter  set like a personal letter                 open     more space, open questions
#   light   a brighter, open window
OPENINGS = {1: "screen", 2: "window", 4: "dark", 5: "presence", 6: "gap", 8: "stack",
            11: "open", 12: "letter", 13: "light"}

# The few lines set apart in the text itself.
SPECIALS = [
    (14, ["وأنا، يا شهد، ما زلت أحاول أن أجد الكلمات."], "fade"),
    (14, ["وما زلت هنا."], "last"),
]

NAVY, WINE, FOG = "#17263B", "#754A53", "#A7A7A0"


def esc(s):
    return html.escape(s, quote=True)


def css_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ar(n):
    return str(n).translate(AR_DIGITS)


def lines_html(text):
    return "<br>".join(esc(line) for line in text.split("\n"))


# ---------------------------------------------------------------- manuscript

def parse(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    book = {
        "title": paras[0].strip("«» "),
        "subtitle": paras[1],
        "intro": paras[2],
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
    for n, (q, _) in CHAPTER_QUOTES.items():
        assert q in " ".join(book["chapters"][n - 1]["paras"]), f"quote for chapter {n} not found"
    for n, group, _ in SPECIALS:
        ps = book["chapters"][n - 1]["paras"]
        assert any(ps[i:i + len(group)] == group for i in range(len(ps))), f"special in chapter {n} not found"
    return book


# ---------------------------------------------------------------- styles

FONTS_CSS = """
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Bold.ttf); font-weight: 700; }
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Italic.ttf); font-style: italic; }
@font-face { font-family: 'Alexandria'; src: url(fonts/Alexandria-300.ttf); font-weight: 300; }
@font-face { font-family: 'Alexandria'; src: url(fonts/Alexandria-400.ttf); font-weight: 400; }
@font-face { font-family: 'Alexandria'; src: url(fonts/Alexandria-600.ttf); font-weight: 600; }
@font-face { font-family: 'Plex'; src: url(fonts/IBMPlexSansArabic-300.ttf); font-weight: 300; }
@font-face { font-family: 'Plex'; src: url(fonts/IBMPlexSansArabic-400.ttf); font-weight: 400; }
@font-face { font-family: 'Plex'; src: url(fonts/IBMPlexSansArabic-500.ttf); font-weight: 500; }
"""

BASE_CSS = """
:root { --navy: #17263B; --paper: #EDE5D9; --wine: #754A53; --fog: #A7A7A0; --ivory: #F7F4EE;
        --text: #1d2734; --muted: #7e7f7c; --hair: #c9c1b4; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body { font-family: 'Amiri', serif; color: var(--text); font-size: 11.5pt; line-height: 1.6;
       font-kerning: normal; text-rendering: optimizeLegibility; }

@page { size: 148mm 210mm; margin: 17mm 17.5mm; }
@page :blank { @top-center { content: none; } @bottom-center { content: none; } }
@page sheet { margin: 0; @top-center { content: none; } @bottom-center { content: none; } }

/* full-page sheets; ones without a background let the paper show through */
.sheet { page: sheet; width: 148mm; height: 210mm; position: relative; overflow: hidden;
         break-after: page; break-inside: avoid; display: flex; flex-direction: column;
         align-items: center; justify-content: center; text-align: center; }
.sheet.navy { background: url(art/navy.jpg) center / cover; color: var(--ivory); }
.marker { position: absolute; top: 2mm; left: 2mm; font-size: 2pt; line-height: 1; color: rgba(0,0,0,.02); }
.hair { width: 12mm; height: 0; border-top: 0.3mm solid var(--wine); margin: 0 auto; }

/* ---- covers */
.cover { background: url(art/cover.jpg) center / cover; color: var(--ivory); justify-content: flex-start; }
.cover .title { margin-top: 36mm; font-family: 'Alexandria'; line-height: 1.25; }
.cover .title .a { display: block; font-weight: 300; font-size: 21pt; opacity: .9; }
.cover .title .b { display: block; font-weight: 600; font-size: 46pt; }
.cover .hair { margin-top: 7mm; border-color: #a77c86; }
.cover .sub { margin-top: 5mm; font-family: 'Plex'; font-weight: 300; font-size: 10.5pt; opacity: .82; }
.cover .author { position: absolute; bottom: 14mm; left: 0; right: 0; font-family: 'Plex'; font-weight: 500;
                 font-size: 10pt; opacity: .88; }
.back { background: url(art/back.jpg) center / cover; color: var(--ivory); justify-content: flex-start; }
.back .blurb { margin-top: 48mm; padding: 0 21mm; text-align: justify; font-size: 10.5pt; line-height: 1.85; }
.back .blurb p { margin: 0 0 3.2mm; opacity: .9; }
.back .blurb p:last-child { margin-top: 5mm; text-align: center; font-size: 12pt; opacity: 1; }

/* ---- front matter */
.half-title .t { font-family: 'Alexandria'; font-weight: 600; font-size: 17pt; color: var(--navy); }
.title-page .title { font-family: 'Alexandria'; color: var(--navy); line-height: 1.25; margin-top: -10mm; }
.title-page .title .a { display: block; font-weight: 300; font-size: 19pt; }
.title-page .title .b { display: block; font-weight: 600; font-size: 40pt; }
.title-page .hair { margin-top: 7mm; }
.title-page .sub { margin-top: 5mm; font-family: 'Plex'; font-weight: 300; font-size: 10.5pt; color: var(--muted); }
.title-page .author { position: absolute; bottom: 22mm; left: 0; right: 0; font-family: 'Plex'; font-weight: 500;
                      font-size: 10pt; color: var(--navy); }
.colophon { justify-content: flex-end; padding: 0 24mm 26mm; font-family: 'Plex'; font-weight: 300;
            font-size: 7.5pt; line-height: 2; color: var(--muted); }
.colophon .t { font-weight: 500; font-size: 9pt; color: var(--navy); }
.colophon .hair { border-color: var(--hair); margin: 3mm auto; width: 10mm; }
.dedication { padding: 0 22mm; }
.dedication p { margin: 0 0 6mm; font-size: 12pt; line-height: 1.95; }
.dedication p.to { color: var(--wine); font-size: 13pt; }
.quote-page { padding: 0 24mm; }
.quote-page p { margin: 0; font-size: 14pt; line-height: 2; color: var(--navy); }
.quote-page .hair { margin-bottom: 8mm; }
.quote-page.small p { font-size: 11.5pt; color: var(--text); }
.quote-page.small .hair { width: 6mm; }
.separator p { margin: 0; font-size: 15pt; line-height: 2; color: var(--navy); padding: 0 24mm; }
.separator .dot { width: 1.6mm; height: 1.6mm; border-radius: 50%; background: var(--fog); margin: 9mm auto 0; }
.intro { padding: 0 22mm; }
.intro p { margin: 0; font-size: 12.5pt; line-height: 2; }
.toc { justify-content: flex-start; padding: 26mm 18mm 0; }
.toc h2 { font-family: 'Alexandria'; font-weight: 600; font-size: 15pt; color: var(--navy); margin: 0 0 9mm; }
.toc ol { list-style: none; margin: 0; padding: 0; width: 100%; }
.toc li { display: flex; align-items: baseline; gap: 2.5mm; padding: 1.1mm 0; font-size: 10.5pt; line-height: 1.55; }
.toc .num { flex: 0 0 7mm; color: var(--wine); text-align: right; }
.toc .dots { flex: 1; border-bottom: 0.25mm dotted var(--fog); transform: translateY(-1.2mm); min-width: 6mm; }
.toc .pg { color: var(--muted); }

/* ---- chapter start: a fixed first page holding the opening and the first lines of text */
.start { justify-content: flex-start; align-items: stretch; text-align: right; }
.start .head { flex: none; height: 64mm; display: flex; flex-direction: column; justify-content: flex-end;
               align-items: center; text-align: center; padding-bottom: 8mm; }
.start.open .head { height: 82mm; }
.start .vig { margin-bottom: 7mm; }
.start .vig svg { display: block; height: 15mm; width: auto; }
.start .num { font-family: 'Alexandria'; font-weight: 300; font-size: 9pt; color: var(--muted); }
.start .ttl { font-family: 'Alexandria'; font-weight: 600; font-size: 18pt; line-height: 1.5; color: var(--navy);
              margin-top: 2mm; max-width: 100mm; }
.start .rule { width: 10mm; border-top: 0.25mm solid var(--hair); margin-top: 5mm; }
.start .flow { flex: 1; overflow: hidden; }
.start.cont-only .head { height: 4mm; padding: 0; }

.dark-opener .num { font-family: 'Alexandria'; font-weight: 300; font-size: 9pt; color: var(--fog); }
.dark-opener .ttl { font-family: 'Alexandria'; font-weight: 600; font-size: 20pt; line-height: 1.5; margin-top: 3mm;
                    max-width: 100mm; color: var(--ivory); }
.dark-opener .hair { margin-top: 7mm; border-color: #a77c86; }

/* ---- chapter text */
.chapter-body { break-before: page; }
.text p, .flow p { margin: 0 0 1.3mm; text-indent: 1.4em; text-align: justify; widows: 2; orphans: 2; }
.text p.first, .flow p.first, .text p.cont, .flow p.cont { text-indent: 0; }
.flow p.split-a { text-align-last: justify; margin-bottom: 0; }
.end-mark { width: 8mm; border-top: 0.3mm solid var(--wine); margin: 7mm auto 0; opacity: .7; }
.sp { break-inside: avoid; margin: 7mm 0; text-align: center; text-indent: 0; }
.sp.fade { font-size: 13pt; }
.sp.last { font-size: 16pt; color: var(--navy); margin-top: 10mm; }

/* a chapter set like a personal letter: wider margins, a slightly more intimate hand */
.letter .flow p, .letter-body .text p { font-style: italic; font-size: 12pt; line-height: 1.7; }

/* ---- endings */
.khatima { padding: 0 22mm; }
.khatima h2 { font-family: 'Alexandria'; font-weight: 600; font-size: 15pt; color: var(--navy); margin: 0 0 3mm; }
.khatima .hair { margin-bottom: 8mm; }
.khatima p { margin: 0 0 3.5mm; font-size: 11.5pt; line-height: 1.9; }
.closing { padding: 0 24mm; }
.closing p { margin: 0 0 4mm; font-size: 13pt; line-height: 2; color: var(--navy); }
.closing p.end1 { margin-top: 8mm; }
.closing p.end2 { color: var(--wine); }
"""

PRINT_CSS = """
@page :left  { margin-left: 15mm; margin-right: 20mm; }
@page :right { margin-left: 20mm; margin-right: 15mm; }
@page ch12:left  { margin-left: 21mm; margin-right: 26mm; }
@page ch12:right { margin-left: 26mm; margin-right: 21mm; }
.start { padding: 17mm 20mm 17mm 15mm; }            /* chapters open on recto pages: binding on the right */
.start.letter { padding: 17mm 26mm 17mm 21mm; }
"""

SCREEN_CSS = """
@page ch12 { margin-left: 23.5mm; margin-right: 23.5mm; }
.start { padding: 17mm 17.5mm; }
.start.letter { padding: 17mm 23.5mm; }
"""

# Moves the first lines of each chapter onto its opening page, splitting the last paragraph
# between words, so the text runs on without a gap. Runs in print layout before the PDF is made.
FILL_JS = """
window.__bookReady = false;
document.fonts.ready.then(() => {
  const SAFETY = 6;  // px kept free at the foot of the page
  for (const ch of document.querySelectorAll('.chapter')) {
    const flow = ch.querySelector('.start .flow');
    const body = ch.querySelector('.chapter-body .text');
    if (!flow || !body) continue;
    const fits = () => {
      const last = flow.lastElementChild;
      if (!last) return true;
      return last.getBoundingClientRect().bottom - flow.getBoundingClientRect().top <= flow.clientHeight - SAFETY;
    };
    while (body.firstElementChild) {
      const el = body.firstElementChild;
      flow.appendChild(el);
      if (fits()) continue;
      if (el.tagName === 'P') {
        const words = el.textContent.split(' ');
        let lo = 0, hi = words.length;
        while (lo < hi) {
          const mid = Math.ceil((lo + hi) / 2);
          el.textContent = words.slice(0, mid).join(' ');
          if (fits()) lo = mid; else hi = mid - 1;
        }
        if (lo > 0 && lo < words.length) {
          el.textContent = words.slice(0, lo).join(' ');
          el.classList.add('split-a');
          const rest = document.createElement('p');
          rest.className = 'cont';
          rest.textContent = words.slice(lo).join(' ');
          body.prepend(rest);
        } else {
          el.textContent = words.join(' ');
          body.prepend(el);
        }
      } else {
        body.prepend(el);
      }
      break;
    }
    if (!body.firstElementChild && !ch.querySelector('.chapter-body .end-mark')) {
      ch.querySelector('.chapter-body').remove();
    }
  }
  window.__bookReady = true;
});
"""


def page_css(book):
    """Running heads: the novel's title on even pages, the chapter's title on odd pages."""
    head = ("font-family: 'Plex'; font-weight: 400; font-size: 7pt; color: #8f8f88; "
            "vertical-align: bottom; padding-bottom: 6mm;")
    foot = ("content: counter(page, arabic-indic); font-family: 'Plex'; font-weight: 400; font-size: 8.5pt; "
            "color: #7e7f7c; vertical-align: top; padding-top: 6mm;")
    rules = [
        f"@page :right {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page :left {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page {{ @bottom-center {{ {foot} }} }}",
    ]
    for n, ch in enumerate(book["chapters"], 1):
        rules.append(f"@page ch{n}:left {{ @top-center {{ content: {css_str(ch['title'])}; {head} }} }}")
    return "\n".join(rules)


# ---------------------------------------------------------------- small abstract marks

def vignette(kind):
    n, w, f = NAVY, WINE, FOG
    if kind == "screen":
        return (f'<svg viewBox="0 0 60 40"><rect x="8" y="6" width="44" height="28" rx="5" fill="#f3eee6" '
                f'stroke="{f}" stroke-width="1.2"/><rect x="26" y="19" width="8" height="1.4" rx=".7" fill="{w}"/></svg>')
    if kind in ("window", "light"):
        fill = "#e8d9bf" if kind == "window" else "#faf7f1"
        glow = "" if kind == "window" else '<circle cx="30" cy="20" r="19" fill="#fffdf8" opacity=".55"/>'
        return (f'<svg viewBox="0 0 60 40">{glow}<rect x="21" y="5" width="18" height="26" fill="{fill}" stroke="{n}" '
                f'stroke-width="1.4"/><line x1="30" y1="5" x2="30" y2="31" stroke="{n}" stroke-width="1.1"/>'
                f'<line x1="21" y1="16" x2="39" y2="16" stroke="{n}" stroke-width="1.1"/>'
                f'<rect x="19" y="31" width="22" height="1.6" fill="{n}"/></svg>')
    if kind == "presence":
        return (f'<svg viewBox="0 0 60 40"><line x1="12" y1="20" x2="48" y2="20" stroke="{f}" stroke-width=".6"/>'
                f'<circle cx="38" cy="20" r="3.4" fill="{n}"/>'
                f'<circle cx="22" cy="20" r="3.2" fill="none" stroke="{n}" stroke-width=".8" stroke-dasharray="1.4 1.2"/></svg>')
    if kind == "gap":
        return (f'<svg viewBox="0 0 60 40"><rect x="7" y="14" width="18" height="12" fill="{n}"/>'
                f'<rect x="35" y="14" width="18" height="12" fill="{n}"/>'
                f'<line x1="3" y1="20" x2="57" y2="20" stroke="{w}" stroke-width=".9"/></svg>')
    if kind == "stack":
        rects = "".join(f'<rect x="{18 + i * 3}" y="{24 - i * 4.5}" width="22" height="9" fill="#efe9df" '
                        f'stroke="{n if i == 3 else f}" stroke-width="{1.1 if i == 3 else .8}"/>' for i in range(4))
        return f'<svg viewBox="0 0 60 40">{rects}</svg>'
    return ""


# ---------------------------------------------------------------- pages

class Ctx:
    """What a render pass needs to know: whether to stamp page markers, and before which
    pages to add a blank page so that each lands on the side it belongs (print only)."""

    def __init__(self, mode, toc_pages=None, markers=False, blanks=()):
        self.mode, self.toc_pages, self.markers, self.blanks = mode, toc_pages or {}, markers, set(blanks)

    def at(self, key):
        """(html before the sheet, html inside it) for a marked sheet."""
        before = '<div class="sheet blank"></div>' if key in self.blanks else ""
        inside = f'<span class="marker">QZ{key}QZ</span>' if self.markers else ""
        return before, inside


def side_of(key):
    """Which side of a spread a marked page must fall on in print: odd (left, recto) or even."""
    if key == "HT":
        return None
    return "even" if key.startswith("Q") else "odd"   # quote pages face the chapter that follows


def title_block():
    return '<div class="title"><span class="a">ما زلتُ</span><span class="b">أختاركِ</span></div>'


def cover_front(book):
    return f"""
<div class="sheet cover">
  {title_block()}
  <div class="hair"></div>
  <div class="sub">{esc(book['subtitle'])}</div>
  <div class="author">{esc(AUTHOR)}</div>
</div>"""


def cover_back():
    paras = "".join(f"<p>{esc(p)}</p>" for p in BACK_BLURB)
    return f'<div class="sheet back"><div class="blurb">{paras}</div></div>'


def front_matter(book, ctx):
    out = []
    if ctx.mode == "print":
        _, mk = ctx.at("HT")
        out.append(f'<div class="sheet half-title">{mk}<div class="t">{esc(book["title"])}</div></div>')
    b, mk = ctx.at("TI")
    out.append(f"""{b}
<div class="sheet title-page">{mk}
  {title_block()}
  <div class="hair"></div>
  <div class="sub">{esc(book['subtitle'])}</div>
  <div class="author">{esc(AUTHOR)}</div>
</div>""")
    out.append(f"""
<div class="sheet colophon">
  <div class="t">{esc(book['title'])}</div>
  <div>{esc(book['subtitle'])}</div>
  <div class="hair"></div>
  <div>© {esc(AUTHOR)}، {ar(YEAR)}</div>
  <div>جميع الحقوق محفوظة للمؤلف</div>
  <div>الطبعة الأولى</div>
  <div class="hair"></div>
  <div>الخطوط: أميري، الإسكندرية، آي بي إم بلكس سانس العربي</div>
</div>""")
    ded = book["dedication"]
    b, mk = ctx.at("DE")
    ps = f'<p class="to">{lines_html(ded[0])}</p>' + "".join(f"<p>{lines_html(p)}</p>" for p in ded[1:])
    out.append(f'{b}<div class="sheet dedication">{mk}{ps}</div>')
    b, mk = ctx.at("PR")
    out.append(f'{b}<div class="sheet intro">{mk}<p>{esc(book["intro"])}</p></div>')
    items = []
    for n, ch in enumerate(book["chapters"], 1):
        pg = ar(ctx.toc_pages.get(f"C{n:02d}", 0))
        items.append(f'<li><span class="num">{ar(n)}</span><span class="name">{esc(ch["title"])}</span>'
                     f'<span class="dots"></span><span class="pg">{pg}</span></li>')
    items.append(f'<li><span class="num"></span><span class="name">خاتمة</span>'
                 f'<span class="dots"></span><span class="pg">{ar(ctx.toc_pages.get("KH", 0))}</span></li>')
    b, mk = ctx.at("TO")
    out.append(f'{b}<div class="sheet toc">{mk}<h2>الفهرس</h2><ol>{"".join(items)}</ol></div>')
    b, mk = ctx.at("OQ")
    out.append(f'{b}<div class="sheet quote-page">{mk}<div class="hair"></div>'
               f'<p>{esc(OPENING_QUOTE[0])}<br>{esc(OPENING_QUOTE[1])}</p></div>')
    return "\n".join(out)


def text_paragraphs(n, ch):
    ps = ch["paras"]
    groups = [(g, kind) for c, g, kind in SPECIALS if c == n]
    out = []
    i = 0
    while i < len(ps):
        for g, kind in groups:
            if ps[i:i + len(g)] == g:
                out.append(f'<div class="sp {kind}">{esc(g[0])}</div>')
                i += len(g)
                break
        else:
            out.append(f'<p class="first">{esc(ps[i])}</p>' if i == 0 else f"<p>{esc(ps[i])}</p>")
            i += 1
    return "".join(out)


def chapter(n, ch, ctx, last):
    kind = OPENINGS.get(n, "")
    out = ['<section class="chapter">']
    if n in CHAPTER_QUOTES:
        q, size = CHAPTER_QUOTES[n]
        b, mk = ctx.at(f"Q{n:02d}")
        out.append(f'{b}<div class="sheet quote-page {size}">{mk}<div class="hair"></div><p>{esc(q)}</p></div>')
    b, mk = ctx.at(f"C{n:02d}")
    num = f"الفصل {esc(ch['ordinal'])}"
    title = esc(ch["title"])
    if kind == "dark":
        out.append(f'{b}<div class="sheet navy dark-opener">{mk}<div class="num">{num}</div>'
                   f'<div class="ttl">{title}</div><div class="hair"></div></div>')
        out.append('<div class="sheet start cont-only"><div class="head"></div><div class="flow"></div></div>')
    else:
        vig = vignette(kind)
        vig = f'<div class="vig">{vig}</div>' if vig else ""
        out.append(f'{b}<div class="sheet start {kind}">{mk}<div class="head">{vig}<div class="num">{num}</div>'
                   f'<div class="ttl">{title}</div><div class="rule"></div></div><div class="flow"></div></div>')
    body_cls = "chapter-body letter-body" if kind == "letter" else "chapter-body"
    end = "" if last else '<div class="end-mark"></div>'
    out.append(f'<div class="{body_cls}" style="page: ch{n}"><div class="text">{text_paragraphs(n, ch)}</div>{end}</div>')
    out.append("</section>")
    if n in SEPARATORS:
        b, mk = ctx.at(f"S{n:02d}")
        out.append(f'{b}<div class="sheet separator">{mk}<p>{esc(SEPARATORS[n])}</p><div class="dot"></div></div>')
    return "\n".join(out)


def endings(book, ctx):
    b, mk = ctx.at("KH")
    paras = "".join(f"<p>{esc(p)}</p>" for p in book["khatima"])
    out = [f'{b}<div class="sheet khatima">{mk}<h2>خاتمة</h2><div class="hair"></div>{paras}</div>']
    b, mk = ctx.at("CL")
    c = CLOSING
    out.append(f'{b}<div class="sheet closing">{mk}<p>{esc(c[0])}</p><p>{esc(c[1])}</p>'
               f'<p class="end1">{esc(c[2])}</p><p class="end2">{esc(c[3])}</p></div>')
    return "\n".join(out)


def document(book, part, ctx):
    css = FONTS_CSS + BASE_CSS + (PRINT_CSS if ctx.mode == "print" else SCREEN_CSS)
    body, script = [], ""
    if part == "cover":
        body += [cover_front(book), cover_back()]
    else:
        css += "\n" + page_css(book)
        body.append(front_matter(book, ctx))
        total = len(book["chapters"])
        for n, ch in enumerate(book["chapters"], 1):
            body.append(chapter(n, ch, ctx, last=(n == total)))
        body.append(endings(book, ctx))
        script = f"<script>{FILL_JS}</script>"
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>{esc(book['title'])}</title>
<style>{css}</style></head>
<body>{''.join(body)}{script}</body>
</html>"""


# ---------------------------------------------------------------- build

def render(html_text, name):
    src = ROOT / f"_{name}.html"  # next to fonts/ and art/ so relative URLs resolve
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
    return pages


def expected_keys(book, mode):
    keys = (["HT"] if mode == "print" else []) + ["TI", "DE", "PR", "TO", "OQ"]
    for n in range(1, len(book["chapters"]) + 1):
        if n in CHAPTER_QUOTES:
            keys.append(f"Q{n:02d}")
        keys.append(f"C{n:02d}")
        if n in SEPARATORS:
            keys.append(f"S{n:02d}")
    return keys + ["KH", "CL"]


def lay_on_paper(pdf_in, pdf_out, ivory_pages):
    """Puts the paper texture under every page: ivory for the title pages, warm paper elsewhere.
    (Chromium only paints @page backgrounds inside the margins, so it goes underneath afterwards.)"""
    tex = {k: PdfReader(ART / f"{k}.pdf").pages[0] for k in ("paper", "ivory")}
    writer = PdfWriter()
    for i, page in enumerate(PdfReader(pdf_in).pages, 1):
        t = tex["ivory" if i in ivory_pages else "paper"]
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        base = writer.add_blank_page(width=w, height=h)
        base.merge_transformed_page(t, Transformation().scale(w / float(t.mediabox.width),
                                                              h / float(t.mediabox.height)))
        base.merge_page(page)
    writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
    with open(pdf_out, "wb") as f:
        writer.write(f)


def build_interior(book, mode):
    """Locate the pages that must fall on a given side, add blank pages where needed (print only),
    then fill the table of contents with the final page numbers."""
    keys = expected_keys(book, mode)
    pages = find_markers(render(document(book, "interior", Ctx(mode, markers=True)), f"{mode}-probe"))
    missing = set(keys) - set(pages)
    if missing:
        sys.exit(f"could not locate pages for: {sorted(missing)}")
    blanks = []
    if mode == "print":
        # Every marked page starts a fresh sheet, so a blank page only shifts what follows.
        shift = 0
        for key in keys:
            want = side_of(key)
            if want and (pages[key] + shift) % 2 != (1 if want == "odd" else 0):
                blanks.append(key)
                shift += 1
    probe = render(document(book, "interior", Ctx(mode, markers=True, blanks=blanks)), f"{mode}-probe2")
    pages = find_markers(probe)
    if mode == "print":
        wrong = [k for k in keys if side_of(k) and pages[k] % 2 != (1 if side_of(k) == "odd" else 0)]
        if wrong:
            sys.exit(f"pages on the wrong side: {wrong}")
    pdf = render(document(book, "interior", Ctx(mode, pages, blanks=blanks)), f"{mode}-interior")
    if page_count(pdf) != page_count(probe):
        sys.exit("pagination changed between passes")
    ivory = {pages[k] for k in ("HT", "TI", "DE") if k in pages}
    textured = BUILD / f"{mode}-interior-paper.pdf"
    lay_on_paper(pdf, textured, ivory)
    return textured, pages


def main():
    if not (ART / "paper.pdf").exists():
        subprocess.run([sys.executable, str(ROOT / "illustrate.py")], check=True)
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
        print(f"{k:9s} {page_count(p):3d} pages  {p.stat().st_size / 1e6:5.1f} MB  {p.relative_to(ROOT)}")
    print("marked pages (print):", {k: v for k, v in sorted(print_pages.items(), key=lambda kv: kv[1])})


if __name__ == "__main__":
    main()
