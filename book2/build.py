#!/usr/bin/env python3
"""Builds «ما زلت خائفًا، ما زلت وحيدًا» from manuscript.txt into designed, print-ready PDFs,
in the system of the first novel (../book): old paper, a picture opening each chapter, the title
as lettering, and a few moments where the words act out what they say. This book is colder:
ash-grey paper, charcoal instead of rose, and one warm amber light.

Outputs (in ./output):
  ma-zilt-khaifan-print-interior.pdf  A5 interior for the printer (chapters open on recto pages)
  ma-zilt-khaifan-cover.pdf           front and back cover, A5
  ma-zilt-khaifan-screen.pdf          cover + interior + back cover, for reading on screens

Usage: python3 build.py   (draws ./art with illustrate.py first if it is missing)
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
RENDER_JS = ROOT.parent / "book" / "render.js"
FONTS = "../book/fonts"

AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
AUTHOR = "بهاء الدين أبو زبيدة"
SLUG = "ma-zilt-khaifan"

# The line before the first chapter.
EPIGRAPH = "لم أكن أعرف أن هناك أسئلة لا تأتي لتُجاب، بل لتبقى في الإنسان وتغيّر شكله إلى الأبد."

# On the back cover, all taken from the last chapter.
BACK_HOOK = "كنت في السادسة عشرة."
BACK_TEXT = [
    "هذه ليست حكاية شخص انتصر على كل شيء.",
    "وليست حكاية شخص هزمته الحياة تمامًا.",
    "إنها حكاية إنسان ما زال يحاول أن يفهم ما حدث له، وأن يجد لنفسه مكانًا في عالم لم يعد يشبه العالم الذي عرفه.",
]

# A key line from each chapter, shown on its opening page (verbatim from the chapter).
QUOTES = {
    1: ["أحيانًا يكون العقل قد تلقّى أكثر مما يستطيع أن يفهم، فيختار ألّا يفهم شيئًا."],
    2: ["لقد فعل أمرًا بسيطًا للغاية: لم يطلب مني أن أتوقف عن الحزن."],
    3: ["لكن وجود أشخاص يعتمدون عليك يجعل حتى العجز مضطرًا إلى الوقوف."],
    4: ["ثمة فرق بين أن تكون محاطًا بالناس، وأن يكون هناك من يحمل معك ما لا تستطيع حمله."],
    5: ["لكن عودة الأشخاص لا تعني عودة الزمن، ونجاة من تحب لا تمحو من فقدتهم في غيابه."],
    6: ["لكن بعض الكلمات لا نعرف قيمتها إلا بعد أن يصبح الرد عليها مستحيلًا."],
    7: ["هناك فرحة تحتاج إلى وجوه بعينها حتى تكتمل."],
    8: ["كان جرحًا يتلقى جرحًا جديدًا قبل أن يعرف كيف يتعامل مع السابق."],
    9: ["لم يكن أكثر ما يؤلمني أنني تُركت وحدي؛ بل أنني بدأت أشعر بأن عليّ أن أكون أقل وجعًا كي أستحق بقاء أحد."],
    10: ["لكن الحزن لا يلتزم بالمدة التي تمنحها له."],
    11: ["ثم فهمت أن هناك خسارات أخرى لا جنازة لها."],
    12: ["أن القرب يمكن أن يكون قربًا، لا مهلة قصيرة بين خسارتين."],
    13: ["ليس كل ألم يتراجع في خط مستقيم، وليس كل ما ننجو منه ينتهي بمجرد أن نبتعد عنه."],
    14: ["أن أفتح نافذة، ولو صغيرة، في جدار السنوات الماضية."],
}

# Moments set apart in the text: consecutive paragraphs of a chapter (verbatim) and how they are set.
SPECIALS = [
    (1, ["ثم جاءت الحرب."], "war"),
    (1, ["استشهد أحمد، واستشهدت أختاه، جَنّات وروان."], "names"),
    (2, ["لن تجلس عمتي شهيرة بيننا كما كانت.", "لن يعود أحمد إلى البيت.", "لن تعود أخواته."], "absence"),
    (3, ["كيف سأحميهم؟", "أين سننام؟", "ماذا سنأكل؟", "كيف سأتصرف إذا حدث شيء آخر؟"], "scatter"),
    (5, ["لماذا غادرت؟", "لماذا نمت؟", "لماذا لم تبقَ؟"], "louder"),
    (6, ["«سامحني يا بهاء، تعبتك معي»."], "voice"),
    (6, ["كان عليّ أن أرى.", "أن أساعد.", "أن أخرج.", "أن أدفن.", "ثم أعود."], "stairs"),
    (8, ["أتذكر صورهم.", "أتذكر وجوههم.", "أتذكر القبور التي حفرتها بيديّ."], "remember"),
    (8, ["لكنني مررت.", "وما زلت هنا."], "survived"),
    (10, ["كنت أريد أن أقول: أنا أقدّر أنك بقيت.", "لكنني ما زلت أتألم.", "الجملتان صحيحتان معًا.",
          "ولا تلغي إحداهما الأخرى."], "balance"),
    (12, ["من التالي الذي سأفقده؟", "من التالي الذي سأضطر إلى توديع صورته بدلًا من توديعه؟",
          "ومن التالي الذي سأتعلم كيف أعيش من دونه، بينما لم أتعلم بعد كيف أعيش من دون الذين سبقوه؟"], "next"),
    (14, ["أنا."], "alone"),
    (14, ["حزينًا، من دون أن يكون عبئًا.", "خائفًا، من دون أن يكون ضعيفًا.",
          "وحيدًا أحيانًا، من دون أن تكون الوحدة قدره الأبدي."], "pairs"),
    (14, ["ما زلت خائفًا.", "ما زلت وحيدًا."], "title-echo"),
]

DARK_OPENERS = {5, 8}


def esc(s):
    return html.escape(s, quote=True)


def css_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ar(n):
    return str(n).translate(AR_DIGITS)


# ---------------------------------------------------------------- manuscript

def parse(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    book = {"title": paras[0], "subtitle": paras[1], "dedication": [], "chapters": [], "end": ""}
    i = paras.index("إهداء") + 1
    while paras[i] != "---":
        book["dedication"].append(paras[i])
        i += 1
    i += 1
    chapter_re = re.compile(r"^الفصل (.+?): (.+)$")
    current = None
    for p in paras[i:]:
        m = chapter_re.match(p)
        if m:
            current = {"ordinal": m.group(1), "title": m.group(2), "paras": []}
            book["chapters"].append(current)
        elif p == "---":
            current = None
        elif current is None:
            book["end"] = p
        else:
            current["paras"].append(p)
    assert len(book["chapters"]) == 14, len(book["chapters"])
    assert EPIGRAPH in " ".join(book["chapters"][0]["paras"])
    for n, ch in enumerate(book["chapters"], 1):
        for part in QUOTES[n]:
            assert part in " ".join(ch["paras"]), f"quote for chapter {n} not found: {part}"
    for n, group, kind in SPECIALS:
        ps = book["chapters"][n - 1]["paras"]
        assert any(ps[i:i + len(group)] == group for i in range(len(ps))), f"special '{kind}' in chapter {n} not found"
    return book


# ---------------------------------------------------------------- styles

FONTS_CSS = f"""
@font-face {{ font-family: 'Amiri'; src: url({FONTS}/Amiri-Regular.ttf); font-weight: 400; }}
@font-face {{ font-family: 'Amiri'; src: url({FONTS}/Amiri-Bold.ttf); font-weight: 700; }}
@font-face {{ font-family: 'Amiri'; src: url({FONTS}/Amiri-Italic.ttf); font-style: italic; }}
@font-face {{ font-family: 'Aref Ruqaa'; src: url({FONTS}/ArefRuqaa-Regular.ttf); font-weight: 400; }}
@font-face {{ font-family: 'Aref Ruqaa'; src: url({FONTS}/ArefRuqaa-Bold.ttf); font-weight: 700; }}
@font-face {{ font-family: 'Reem Kufi'; src: url({FONTS}/ReemKufi-Regular.ttf); font-weight: 400; }}
@font-face {{ font-family: 'Gulzar'; src: url({FONTS}/Gulzar-Regular.ttf); }}
@font-face {{ font-family: 'Lalezar'; src: url({FONTS}/Lalezar-Regular.ttf); }}
@font-face {{ font-family: 'Cormorant'; src: url({FONTS}/CormorantGaramond-MediumItalic.ttf); font-style: italic; }}
"""

BASE_CSS = """
:root { --ink: #2a2826; --muted: #7d7873; --hair: #c2bcb3; --amber: #a2703a; --char: #3a3734; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body { font-family: 'Amiri', serif; color: var(--ink); font-size: 11.5pt; line-height: 1.9;
       font-kerning: normal; text-rendering: optimizeLegibility; }

@page { size: 148mm 210mm; margin: 21mm 17mm 23mm 17mm; }
@page :blank { @top-center { content: none; } @bottom-center { content: none; } }
@page sheet { margin: 0; @top-center { content: none; } @bottom-center { content: none; } }
@page :left  { margin-left: 15mm; margin-right: 20mm; }
@page :right { margin-left: 20mm; margin-right: 15mm; }

.sheet { page: sheet; width: 148mm; height: 210mm; position: relative; overflow: hidden;
         break-after: page; break-inside: avoid; display: flex; flex-direction: column;
         align-items: center; justify-content: center; text-align: center; }
.sheet.art { background-size: cover; background-position: center; }
.marker { position: absolute; top: 2mm; left: 2mm; font-size: 2pt; line-height: 1; color: rgba(0,0,0,.02); }
.strip { display: block; margin: 0 auto; height: auto; }

/* ---- the title as lettering: two halves, «ما زلتُ» on a charcoal brush stroke each time */
.lettering { position: relative; width: 124mm; color: var(--ink); direction: rtl; }
.lettering .row { display: flex; align-items: center; gap: 2.5mm; white-space: nowrap; }
.lettering .r1 { justify-content: flex-start; padding-right: 4mm; }
.lettering .r2 { justify-content: flex-end; margin-top: -3mm; padding-left: 2mm; }
.lettering .still { font-family: 'Lalezar'; font-size: 20pt; line-height: 1.5; color: #efebe4; padding: 0.6mm 5mm 0;
                    background: url(art/brush.png) center / 100% 100% no-repeat; }
.lettering .big { font-family: 'Gulzar'; font-size: 54pt; line-height: 1.45; }
.lettering .en { position: absolute; left: 2mm; top: 4mm; font-family: 'Cormorant'; font-style: italic; font-size: 10pt;
                 line-height: 1.35; direction: ltr; text-align: left; color: #4a4642; }
.lettering .en b { font-weight: normal; background: var(--char); color: #efebe4; padding: 0 1.1mm; }

.cover { justify-content: flex-start; }
.cover .lettering { position: absolute; top: 16mm; left: 12mm; }
.cover .side { position: absolute; top: 34mm; left: 9mm; display: flex; flex-direction: column; align-items: center; gap: 2.5mm; }
.cover .side .bar { width: 0.35mm; height: 16mm; background: var(--amber); }
.cover .side .v { writing-mode: vertical-rl; font-family: 'Reem Kufi'; font-size: 8.5pt; color: var(--ink); }
.cover .author { position: absolute; top: 74mm; left: 0; right: 0; font-family: 'Aref Ruqaa'; font-weight: 700;
                 font-size: 15pt; color: var(--amber); }
.cover .sub { position: absolute; bottom: 14mm; left: 18mm; right: 18mm; font-size: 10.5pt; line-height: 1.8; color: #57524d; }
.cover .sub::before { content: ""; display: block; width: 10mm; margin: 0 auto 3mm; border-top: 0.3mm solid var(--amber); }

.back { justify-content: flex-start; }
.back .vt { position: absolute; top: 20mm; right: 12mm; writing-mode: vertical-rl; font-family: 'Gulzar';
            font-size: 21pt; color: var(--ink); }
.back .rule { position: absolute; top: 24mm; right: 28mm; width: 0.3mm; height: 96mm; background: var(--hair); }
.back .hook { position: absolute; top: 30mm; right: 36mm; left: 18mm; text-align: right; font-family: 'Aref Ruqaa';
              font-weight: 700; font-size: 19pt; color: var(--ink); }
.back .blurb { position: absolute; top: 52mm; right: 36mm; left: 18mm; text-align: justify; font-size: 12pt;
               line-height: 2.05; color: var(--ink); }
.back .blurb p { margin: 0 0 3mm; }
.back .mark { position: absolute; bottom: 50mm; left: 0; right: 0; font-family: 'Reem Kufi'; font-size: 8pt; color: var(--muted); }
.back .mark .a { display: block; margin-top: 1.5mm; font-family: 'Aref Ruqaa'; font-size: 12pt; color: var(--amber); }

/* ---- front matter */
.half-title h2 { font-family: 'Gulzar'; font-weight: 400; font-size: 22pt; margin: 0; color: var(--ink); }
.title-page { justify-content: flex-start; padding-top: 34mm; }
.title-page .kicker { font-family: 'Reem Kufi'; font-size: 9.5pt; color: var(--amber); margin-bottom: 4mm; }
.title-page .lettering { transform: scale(.86); transform-origin: top center; }
.title-page .sub { margin-top: -2mm; font-size: 12pt; color: var(--muted); max-width: 96mm; line-height: 1.8; }
.title-page .author { margin-top: 5mm; font-family: 'Aref Ruqaa'; font-size: 14pt; color: var(--amber); }
.title-page .strip { position: absolute; bottom: 24mm; left: 0; right: 0; width: 84mm; }
.colophon { justify-content: flex-end; padding: 0 24mm 30mm; font-size: 8.5pt; line-height: 2; color: var(--muted); }
.colophon .t { font-family: 'Aref Ruqaa'; font-size: 12pt; color: var(--ink); }
.colophon hr { width: 14mm; border: 0; border-top: 0.3mm solid var(--hair); margin: 4mm auto; }
.dedication { padding: 0 22mm; }
.dedication h2, .toc h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 21pt; margin: 0 0 8mm; }
.dedication p { margin: 0 0 4.2mm; font-size: 11.5pt; line-height: 1.95; }
.dedication p:last-child { margin-top: 3mm; color: var(--amber); }
.prelude { padding: 0 24mm; }
.prelude p { margin: 0; font-size: 14pt; line-height: 2.2; }
.prelude p::before, .prelude p::after { color: var(--amber); font-family: 'Aref Ruqaa'; font-size: 20pt; }
.prelude p::before { content: "«"; } .prelude p::after { content: "»"; }
.toc { justify-content: flex-start; padding: 24mm 18mm 0; }
.toc ol { list-style: none; margin: 0; padding: 0; width: 100%; }
.toc li { display: flex; align-items: baseline; gap: 2.5mm; padding: 1.05mm 0; font-size: 10.5pt; line-height: 1.55; }
.toc .num { flex: 0 0 9mm; font-family: 'Aref Ruqaa'; font-size: 13pt; color: var(--amber); text-align: right; }
.toc .name { text-align: right; }
.toc .dots { flex: 1; border-bottom: 0.25mm dotted #aaa298; transform: translateY(-1.2mm); min-width: 6mm; }
.toc .pg { color: var(--muted); font-size: 10pt; }

/* ---- chapter openers */
.opener { justify-content: flex-start; padding: 0 20mm; }
.opener .ord { margin-top: 26mm; font-family: 'Reem Kufi'; font-size: 9.5pt; color: var(--amber); }
.opener h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 24pt; line-height: 1.5; margin: 5mm 0 0; color: var(--ink); }
.opener blockquote { margin: 9mm 4mm 0; font-size: 11.5pt; line-height: 2; color: #66615c; }
.opener blockquote::before { content: ""; display: block; width: 8mm; margin: 0 auto 4mm; border-top: 0.3mm solid var(--amber); }
.opener.dark .ord { color: #d8b07a; }
.opener.dark h2 { color: #eceef2; }
.opener.dark blockquote { color: #aab0ba; }

/* ---- chapter text */
.chapter-body { break-before: page; }
.chapter-body .head { text-align: center; margin: 2mm 0 9mm; }
.chapter-body .head .t { font-family: 'Aref Ruqaa'; font-size: 13pt; color: var(--amber); line-height: 1.6; }
.chapter-body .head .r { width: 12mm; margin: 2.5mm auto 0; border-top: 0.3mm solid var(--hair); }
.chapter-body p { margin: 0; text-indent: 1.4em; text-align: justify; widows: 2; orphans: 2; }
.chapter-body p.first { text-indent: 0; }
.chapter-body p.first::first-line { color: var(--amber); }
.chapter-body .end-mark { margin-top: 8mm; break-inside: avoid; break-before: avoid; }
.chapter-body .end-mark .strip { width: 46mm; }

/* ---- words that act out what they say */
.sp { break-inside: avoid; margin: 7mm 0; text-align: center; text-indent: 0; }
.sp p, .chapter-body .sp p { text-indent: 0; text-align: center; margin: 0; }
.war { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 25pt; line-height: 1.6; color: var(--ink);
       margin: 10mm 0; letter-spacing: 0; }
.war::before, .war::after { content: ""; display: block; height: 0; border-top: 0.25mm solid var(--hair); margin: 3mm 30%; }
.names { font-size: 13pt; line-height: 2; padding: 0 6mm; }
.names::before, .names::after { content: "·"; display: block; color: var(--amber); font-size: 14pt; line-height: 1; }
.absence p { font-size: 12.5pt; line-height: 2.1; }
.scatter { position: relative; height: 50mm; margin: 6mm 0 2mm; }
.scatter p { position: absolute; text-align: center !important; white-space: nowrap; }
.louder p { font-family: 'Aref Ruqaa'; font-weight: 700; line-height: 1.55; }
.voice { font-size: 16pt; line-height: 2; padding: 0 4mm; font-style: italic; }
.voice::before { content: ""; display: block; width: 10mm; margin: 0 auto 3mm; border-top: 0.3mm solid var(--amber); }
.stairs p { text-align: right !important; font-size: 12.5pt; line-height: 1.95; }
.remember p { font-size: 12.5pt; line-height: 2.1; }
.remember p:last-child { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 16pt; margin-top: 1mm !important; }
.survived p { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 19pt; line-height: 1.7; }
.survived p:last-child { color: var(--amber); }
.balance p { font-size: 12.5pt; }
.balance .a { text-align: right !important; }
.balance .b { text-align: left !important; font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 15pt; }
.balance .c { font-size: 11pt; color: var(--muted); margin-top: 3mm !important; }
.balance .d { font-size: 11pt; color: var(--muted); }
.next p { text-align: right !important; font-size: 12pt; line-height: 2; }
.next em { font-style: normal; font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 15pt; color: var(--amber); }
.alone { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 30pt; margin: 14mm 0; }
.pairs .c { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 17pt; line-height: 1.5; margin-top: 3mm !important; }
.pairs .u { font-size: 11pt; color: var(--muted); line-height: 1.7; }
.title-echo { margin: 12mm 0; }
.title-echo p { font-family: 'Gulzar'; font-size: 26pt; line-height: 1.6; }

/* ---- the end */
.end-page { padding: 0 22mm; }
.end-page .strip { width: 84mm; margin-bottom: 8mm; }
.end-page p { margin: 0; font-family: 'Aref Ruqaa'; font-size: 14pt; color: var(--muted); }
"""


def page_css(book):
    """Running heads: the title on right-hand pages, the chapter's title on left-hand pages."""
    head = ("font-family: 'Reem Kufi'; font-size: 7.5pt; color: #96908a; "
            "vertical-align: bottom; padding-bottom: 7mm;")
    foot = ("content: counter(page, arabic-indic); font-family: 'Amiri'; font-size: 9.5pt; "
            "color: #7d7873; vertical-align: top; padding-top: 7mm;")
    rules = [
        f"@page :right {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page :left {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page {{ @bottom-center {{ {foot} }} }}",
    ]
    for n, ch in enumerate(book["chapters"], 1):
        rules.append(f"@page ch{n}:left {{ @top-center {{ content: {css_str(ch['title'])}; {head} }} }}")
    return "\n".join(rules)


# ---------------------------------------------------------------- special settings

def render_special(kind, ps):
    if kind in ("war", "names", "voice", "alone"):
        return f'<div class="sp {kind}">{esc(ps[0])}</div>'
    if kind == "absence":   # each loss a little fainter, like something going out of reach
        rows = "".join(f'<p style="opacity:{1 - i * 0.22:.2f}">{esc(p)}</p>' for i, p in enumerate(ps))
        return f'<div class="sp absence">{rows}</div>'
    if kind == "scatter":   # the questions crowd in, at different sizes and depths
        spots = [(2, 52, 15, 0.95, -2), (14, 8, 12, 0.7, 1.5), (25, 40, 11.5, 0.6, -1), (36, 6, 11, 0.85, 1.5)]
        out = "".join(f'<p style="top:{t}mm;right:{r}%;font-size:{s}pt;opacity:{o};transform:rotate({a}deg)">{esc(p)}</p>'
                      for p, (t, r, s, o, a) in zip(ps, spots))
        return f'<div class="sp scatter">{out}</div>'
    if kind == "louder":    # the same question asked again, harder each time
        rows = "".join(f'<p style="font-size:{13 + i * 4}pt">{esc(p)}</p>' for i, p in enumerate(ps))
        return f'<div class="sp louder">{rows}</div>'
    if kind == "stairs":    # one step down after another: see, help, go out, bury, come back
        rows = "".join(f'<p style="padding-right:{i * 9}mm">{esc(p)}</p>' for i, p in enumerate(ps))
        return f'<div class="sp stairs">{rows}</div>'
    if kind in ("remember", "survived", "title-echo"):
        return f'<div class="sp {kind}">' + "".join(f"<p>{esc(p)}</p>" for p in ps) + "</div>"
    if kind == "balance":   # both sentences are true at once
        return (f'<div class="sp balance"><p class="a">{esc(ps[0])}</p><p class="b">{esc(ps[1])}</p>'
                f'<p class="c">{esc(ps[2])}</p><p class="d">{esc(ps[3])}</p></div>')
    if kind == "next":
        rows = []
        for i, p in enumerate(ps):
            head = "ومن التالي" if p.startswith("ومن التالي") else "من التالي"
            rows.append(f'<p style="padding-right:{i * 7}mm"><em>{esc(head)}</em>{esc(p[len(head):])}</p>')
        return f'<div class="sp next">{"".join(rows)}</div>'
    if kind == "pairs":
        rows = []
        for p in ps:
            first, rest = p.split("، ", 1)
            rows.append(f'<p class="c">{esc(first)}،</p><p class="u">{esc(rest)}</p>')
        return f'<div class="sp pairs">{"".join(rows)}</div>'
    raise ValueError(kind)


# ---------------------------------------------------------------- pages

class Ctx:
    """What a render pass needs to know: whether to stamp page markers, and before which
    recto pages to add a blank page so that they land on a left-hand (odd) page."""

    def __init__(self, mode, toc_pages=None, markers=False, blanks=()):
        self.mode, self.toc_pages, self.markers, self.blanks = mode, toc_pages or {}, markers, set(blanks)

    def recto(self, key):
        before = '<div class="sheet blank"></div>' if key in self.blanks else ""
        inside = f'<span class="marker">QZ{key}QZ</span>' if self.markers else ""
        return before, inside


RECTO_KEYS = ["TI", "DE", "PR", "TO"] + [f"C{n:02d}" for n in range(1, 15)] + ["EN"]


def lettering():
    return """<div class="lettering" role="heading" aria-level="1" aria-label="ما زلت خائفًا، ما زلت وحيدًا">
    <div class="row r1"><span class="still">ما زلتُ</span><span class="big">خائفًا،</span></div>
    <div class="row r2"><span class="still">ما زلتُ</span><span class="big">وحيـــــــدًا</span></div>
    <div class="en">I'm <b>still</b> afraid.<br>I'm <b>still</b> alone.</div>
  </div>"""


def cover_front(book):
    return f"""
<div class="sheet art cover" style="background-image:url(art/cover.jpg)">
  {lettering()}
  <div class="author">{esc(AUTHOR)}</div>
  <div class="sub">{esc(book['subtitle'])}</div>
</div>"""


def cover_back(book):
    paras = "".join(f"<p>{esc(p)}</p>" for p in BACK_TEXT)
    return f"""
<div class="sheet art back" style="background-image:url(art/back.jpg)">
  <div class="vt">{esc(book['title'])}</div>
  <div class="rule"></div>
  <div class="hook">{esc(BACK_HOOK)}</div>
  <div class="blurb">{paras}</div>
  <div class="mark">رواية<span class="a">{esc(AUTHOR)}</span></div>
</div>"""


def front_matter(book, ctx):
    t = esc(book["title"])
    out = []
    if ctx.mode == "print":
        out.append(f'<div class="sheet half-title"><h2>{t}</h2></div>')
    b, mk = ctx.recto("TI")
    out.append(f"""{b}
<div class="sheet title-page">{mk}
  <div class="kicker">رواية</div>
  {lettering()}
  <div class="sub">{esc(book['subtitle'])}</div>
  <div class="author">{esc(AUTHOR)}</div>
  <img class="strip" src="art/end.png" alt="">
</div>""")
    out.append(f"""
<div class="sheet colophon">
  <div class="t">{t}</div>
  <div>رواية</div>
  <hr>
  <div>© {esc(AUTHOR)}</div>
  <div>جميع الحقوق محفوظة للمؤلف</div>
  <div>الطبعة الأولى، {ar(2026)}</div>
  <hr>
  <div>جُمع النص بخطوط أميري، وعارف رقعة، وجلزار</div>
  <div>الرسوم مرسومة خصيصًا لهذه الرواية</div>
</div>""")
    b, mk = ctx.recto("DE")
    paras = "".join(f"<p>{esc(p)}</p>" for p in book["dedication"])
    out.append(f'{b}<div class="sheet dedication">{mk}<h2>إهداء</h2>{paras}</div>')
    b, mk = ctx.recto("PR")
    out.append(f'{b}<div class="sheet prelude">{mk}<p>{esc(EPIGRAPH)}</p></div>')
    items = []
    for n, ch in enumerate(book["chapters"], 1):
        pg = ar(ctx.toc_pages.get(f"C{n:02d}", 0))
        items.append(f'<li><span class="num">{ar(n)}</span><span class="name">{esc(ch["title"])}</span>'
                     f'<span class="dots"></span><span class="pg">{pg}</span></li>')
    b, mk = ctx.recto("TO")
    out.append(f'{b}<div class="sheet toc">{mk}<h2>الفهرس</h2><ol>{"".join(items)}</ol></div>')
    return "\n".join(out)


def chapter_paragraphs(n, ch):
    ps = ch["paras"]
    groups = [(g, kind) for c, g, kind in SPECIALS if c == n]
    out = []
    i = 0
    while i < len(ps):
        for g, kind in groups:
            if ps[i:i + len(g)] == g:
                out.append(render_special(kind, g))
                i += len(g)
                break
        else:
            out.append(f'<p class="first">{esc(ps[i])}</p>' if i == 0 else f"<p>{esc(ps[i])}</p>")
            i += 1
    return "".join(out)


def chapter(n, ch, ctx, last):
    quote = "".join(f"<span>{esc(q)}</span>" for q in QUOTES[n])
    b, mk = ctx.recto(f"C{n:02d}")
    dark = " dark" if n in DARK_OPENERS else ""
    end = "" if last else '<div class="end-mark"><img class="strip" src="art/end.png" alt=""></div>'
    return f"""
<section class="chapter">{b}
  <div class="sheet art opener{dark}" style="background-image:url(art/ch{n:02d}.jpg)">{mk}
    <div class="ord">الفصل {esc(ch['ordinal'])}</div>
    <h2>{esc(ch['title'])}</h2>
    <blockquote>{quote}</blockquote>
  </div>
  <div class="chapter-body" style="page: ch{n}">
    <div class="head"><div class="t">{esc(ch['title'])}</div><div class="r"></div></div>
    {chapter_paragraphs(n, ch)}
    {end}
  </div>
</section>"""


def end_page(book, ctx):
    """The last page: the bench, left empty; he has got up."""
    b, mk = ctx.recto("EN")
    return f"""{b}
<div class="sheet end-page">{mk}
  <img class="strip" src="art/end-empty.png" alt="">
  <p>{esc(book['end'])}</p>
</div>"""


def document(book, part, ctx):
    css = FONTS_CSS + BASE_CSS
    body = []
    if part == "cover":
        body += [cover_front(book), cover_back(book)]
    else:
        css += "\n" + page_css(book)
        body.append(front_matter(book, ctx))
        total = len(book["chapters"])
        for n, ch in enumerate(book["chapters"], 1):
            body.append(chapter(n, ch, ctx, last=(n == total)))
        body.append(end_page(book, ctx))
    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head><meta charset="utf-8"><title>{esc(book['title'])}</title>
<style>{css}</style></head>
<body>{''.join(body)}</body>
</html>"""


# ---------------------------------------------------------------- build

def render(html_text, name):
    src = ROOT / f"_{name}.html"  # beside art/ so relative URLs resolve (fonts come from ../book)
    src.write_text(html_text, encoding="utf-8")
    pdf = BUILD / f"{name}.pdf"
    subprocess.run(["node", str(RENDER_JS), str(src), str(pdf)], check=True)
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


def lay_on_paper(pdf_in, pdf_out):
    """Puts the paper texture under every page (Chromium only paints @page backgrounds
    inside the margins, so the texture goes underneath afterwards)."""
    paper = PdfReader(ART / "paper.pdf").pages[0]
    pw, ph = float(paper.mediabox.width), float(paper.mediabox.height)
    writer = PdfWriter()
    for page in PdfReader(pdf_in).pages:
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        base = writer.add_blank_page(width=w, height=h)
        base.merge_transformed_page(paper, Transformation().scale(w / pw, h / ph))
        base.merge_page(page)
    writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
    with open(pdf_out, "wb") as f:
        writer.write(f)


def build_interior(book, mode):
    """Locate every sheet that must open a spread, add blank pages where needed (print only),
    then fill the table of contents with the final page numbers."""
    pages = find_markers(render(document(book, "interior", Ctx(mode, markers=True)), f"{mode}-probe"))
    blanks = []
    if mode == "print":
        shift = 0   # every recto sheet starts a fresh page, so a blank page only shifts what follows
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
    textured = BUILD / f"{mode}-interior-paper.pdf"
    lay_on_paper(pdf, textured)
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
        "interior": OUT / f"{SLUG}-print-interior.pdf",
        "cover": OUT / f"{SLUG}-cover.pdf",
        "screen": OUT / f"{SLUG}-screen.pdf",
    }
    names["interior"].write_bytes(print_pdf.read_bytes())
    names["cover"].write_bytes(cover_pdf.read_bytes())
    tmp_front, tmp_back = BUILD / "front.pdf", BUILD / "back.pdf"
    subprocess.run(["pdfseparate", "-f", "1", "-l", "1", str(cover_pdf), str(tmp_front)], check=True)
    subprocess.run(["pdfseparate", "-f", "2", "-l", "2", str(cover_pdf), str(tmp_back)], check=True)
    subprocess.run(["pdfunite", str(tmp_front), str(screen_interior), str(tmp_back), str(names["screen"])], check=True)

    for k, p in names.items():
        print(f"{k:9s} {page_count(p):3d} pages  {p.stat().st_size / 1e6:5.1f} MB  {p.relative_to(ROOT)}")
    print("chapter pages (print):", {k: v for k, v in sorted(print_pages.items())})


if __name__ == "__main__":
    main()
