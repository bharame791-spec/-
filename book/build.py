#!/usr/bin/env python3
"""Builds the novel «ما زلتُ أختاركِ» from manuscript.txt into designed, print-ready PDFs.

Outputs (in ./output):
  ma-zilt-akhtaruki-print-interior.pdf  A5 interior for the printer (chapters open on recto pages)
  ma-zilt-akhtaruki-cover.pdf           front and back cover, A5
  ma-zilt-akhtaruki-screen.pdf          cover + interior + back cover, for reading on screens

The illustrations in ./art come from illustrate.py (run it first if ./art is missing).
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

# A key line from each chapter, shown on its opening page. Each part must appear verbatim
# in the chapter text; parts are shown on separate lines.
QUOTES = {
    1: ["كل ما في الأمر أنني تعرّفت إليكِ."],
    2: ["لأن بعض الأشخاص لا يقاس قربهم بعدد الساعات، بل بالمساحة التي يحتلونها في داخلنا."],
    3: ["كنت أريد أن أكون قويًا، لكنني لم أكن أريد أن أضطر إلى أن أكون قويًا أمامكِ أيضًا."],
    4: ["لكن بعض المواقف تترك فينا أثرًا لا يختفي بمجرد أن نتصالح."],
    5: ["لم أكن أحتاج إلى أن تحلّي المشكلة.", "كنت أحتاج إلى أن تكوني معي وأنا أواجهها."],
    6: ["كنت أخاف أن أجد نفسي مضطرًا إلى الاختيار بين بناء مستقبلي وبين إثبات حبي."],
    7: ["لأنني لم أكن أريد الكلمة وحدها.", "كنت أريد الشعور الذي يسبقها."],
    8: ["حين تصبح الشاشة أمامي أكثر هدوءًا من رأسي، أتمنى لو أنني أستطيع أن أوقف التفكير قليلًا."],
    9: ["هذا ليس تقليلًا من حبكِ.", "بل اعتراف بأنني أنا أيضًا أستحق أن أكون بخير."],
    10: ["أنتِ جزء من أيام كثيرة جميلة."],
    11: ["ربما يحتاج الحب، حين تكبر المسؤوليات، إلى أن يتعلم لغة جديدة."],
    12: ["لكنني أعرف أن الصمت لم يكن يومًا الطريقة التي تمنيت أن نحافظ بها على ما بيننا."],
    13: ["الإنسان قد يكون مشغولًا عن الحديث، لكنه ليس بالضرورة مشغولًا عن الحب."],
    14: ["لأن بعض الحكايات لا تنتهي حين نتعب من كتابتها، بل حين نعرف أخيرًا ماذا نريد أن نقول."],
}

# Moments where the words act out what they say. Each entry names consecutive paragraphs
# of a chapter (verbatim) and how they are set.
SPECIALS = [
    (1, ["كان فيكِ شيء يشبهني."], "echo"),
    (1, ["لم أكن أحاربكِ.", "كنت أحاول الوصول إليكِ."], "reach"),
    (2, ["لأن بعض الأشخاص لا يقاس قربهم بعدد الساعات، بل بالمساحة التي يحتلونها في داخلنا."], "pull"),
    (3, ["وهنا تكمن المشكلة."], "rule"),
    (4, ["كنت واقفًا، وفجأة وجدت نفسي على الأرض، ورأسي يرتطم بها."], "fall"),
    (5, ["لكنني لم أجدكِ إلى جانبي في تلك المرة."], "absent"),
    (6, ["كنا ما زلنا نتحدث.", "لم نكن قد قطعنا بعضنا.", "لكن شيئًا ما بدا مختلفًا."], "drift"),
    (7, ["كنت أريد أن أسمع منكِ كلمة «بحبكِ»."], "word"),
    (7, ["أفرح لأنني ما زلت أسمعها منكِ.", "وأتألم لأنني كنت أتمنى أن تأتي قبل أن أطلبها."], "twotone"),
    (8, ["هل قصّرت؟", "هل كان بإمكاني أن أجد وقتًا إضافيًا؟",
         "هل كان يجب أن أؤجل هذا العمل، أو أنهي تلك المهمة في وقت آخر؟",
         "هل كان عليّ أن أتصرف بطريقة مختلفة حتى لا تشعري بأنني ابتعدت؟"], "scatter"),
    (8, ["وماذا عني أنا؟"], "big"),
    (9, ["كنت متعبًا."], "heartbeat"),
    (10, ["أنا لا أريد أن أخسركِ.", "ولا أريد أن أخسر نفسي وأنا أحاول ألّا أخسركِ."], "balance"),
    (11, ["في البداية، كان سؤالي: كيف أجعلكِ تعرفينني كما أنا؟", "ثم أصبح: كيف أجعلكِ تعرفين أنني أحبكِ؟",
          "واليوم، أجد نفسي أمام سؤال مختلف:", "كيف نستطيع أن نبقى قريبين، ونحن نحاول أن نعيش حياتنا؟"], "stairs"),
    (12, ["أنا أحبكِ."], "big-rose"),
    (13, ["أنا ما زلت في الطريق."], "road"),
    (14, ["أحبكِ.", "ولا أعرف ماذا سيحدث لهذا الحب.", "أشتاق إليكِ.",
          "ولا أعرف إن كان اشتياقي وحده كافيًا ليعيد إلينا ما افتقدناه من سهولة القرب.",
          "أريد أن أبقى قريبًا منكِ.", "وأعرف أن القرب لا يصنعه شخص واحد مهما حاول."], "pairs"),
    (14, ["أنا أحبكِ يا شهد."], "big-rose"),
    (14, ["أنا بهاء."], "big-gold"),
    (14, ["وأنا، يا شهد، ما زلت أحاول أن أجد الكلمات."], "fade"),
    (14, ["وما زلت هنا."], "last"),
]

DARK_OPENERS = {8}


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
    for n, group, kind in SPECIALS:
        ps = book["chapters"][n - 1]["paras"]
        assert any(ps[i:i + len(group)] == group for i in range(len(ps))), \
            f"special '{kind}' in chapter {n} not found: {group[0]}"
    return book


# ---------------------------------------------------------------- styles

FONTS_CSS = """
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Bold.ttf); font-weight: 700; }
@font-face { font-family: 'Amiri'; src: url(fonts/Amiri-Italic.ttf); font-style: italic; }
@font-face { font-family: 'Aref Ruqaa'; src: url(fonts/ArefRuqaa-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Aref Ruqaa'; src: url(fonts/ArefRuqaa-Bold.ttf); font-weight: 700; }
@font-face { font-family: 'Reem Kufi'; src: url(fonts/ReemKufi-Regular.ttf); font-weight: 400; }
@font-face { font-family: 'Reem Kufi'; src: url(fonts/ReemKufi-Medium.ttf); font-weight: 500; }
@font-face { font-family: 'Gulzar'; src: url(fonts/Gulzar-Regular.ttf); }
@font-face { font-family: 'Lalezar'; src: url(fonts/Lalezar-Regular.ttf); }
@font-face { font-family: 'Cormorant'; src: url(fonts/CormorantGaramond-MediumItalic.ttf); font-style: italic; }
"""

BASE_CSS = """
:root { --ink: #2e2a27; --muted: #877e75; --hair: #cfc6ba; --rose: #9c4a55; --gold: #96794d; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
html, body { margin: 0; padding: 0; }
body { font-family: 'Amiri', serif; color: var(--ink); font-size: 11.5pt; line-height: 1.9;
       font-kerning: normal; text-rendering: optimizeLegibility; }

@page { size: 148mm 210mm; margin: 21mm 17mm 23mm 17mm; }
@page :blank { @top-center { content: none; } @bottom-center { content: none; } }
@page sheet { margin: 0; @top-center { content: none; } @bottom-center { content: none; } }
@page :left  { margin-left: 15mm; margin-right: 20mm; }
@page :right { margin-left: 20mm; margin-right: 15mm; }

/* full-page designed sheets; plain ones let the paper texture show through */
.sheet { page: sheet; width: 148mm; height: 210mm; position: relative; overflow: hidden;
         break-after: page; break-inside: avoid; display: flex; flex-direction: column;
         align-items: center; justify-content: center; text-align: center; }
.sheet.art { background-size: cover; background-position: center; }
.marker { position: absolute; top: 2mm; left: 2mm; font-size: 2pt; line-height: 1; color: rgba(0,0,0,.02); }
.strip { display: block; margin: 0 auto; height: auto; }

/* ---- covers */
.cover { justify-content: flex-start; }
.cover .side { position: absolute; top: 14mm; left: 8mm; width: 6mm; display: flex; flex-direction: column;
               align-items: center; gap: 2.5mm; }
.cover .side .bar { width: 0.35mm; height: 16mm; background: var(--rose); }
.cover .side .v { writing-mode: vertical-rl; font-family: 'Reem Kufi'; font-size: 8.5pt; color: var(--ink); }
.cover .lettering { position: absolute; top: 17mm; left: 12mm; }

/* the title as lettering: «ما زلتُ» rests on a brush stroke inside the long kashida of «أختـــاركِ» */
.lettering { position: relative; width: 124mm; height: 56mm; color: var(--ink); text-align: center; }
.lettering .big { position: absolute; top: 4mm; left: 0; right: 0; font-family: 'Gulzar'; font-size: 66pt;
                  line-height: 1.35; white-space: nowrap; }
.lettering .brush { position: absolute; top: 4.6mm; right: 36mm; width: 40mm; height: 12mm;
                    background: url(art/brush.png) center / 100% 100% no-repeat; }
.lettering .still { position: absolute; top: 4mm; right: 36mm; width: 40mm; font-family: 'Lalezar'; font-size: 24pt;
                    line-height: 1.55; color: #f4efe7; }
.lettering .wave { position: absolute; top: 47.5mm; left: 30mm; width: 26mm; height: 3mm; }
.lettering .star { position: absolute; top: 46.2mm; left: 58mm; font-size: 9pt; color: var(--rose); }
.lettering .en { position: absolute; top: 43mm; left: 3mm; font-family: 'Cormorant'; font-style: italic; font-size: 10.5pt;
                 line-height: 1.3; direction: ltr; text-align: left; color: #4a443f; }
.lettering .en b { font-weight: normal; background: #964652; color: #f4efe7; padding: 0 1.2mm; }
.cover .sub { position: absolute; bottom: 17mm; left: 18mm; right: 18mm; font-size: 11pt; line-height: 1.8;
              color: #5e5750; }
.cover .author { position: absolute; top: 66mm; right: 22mm; font-family: 'Aref Ruqaa'; font-size: 15pt;
                 color: var(--rose); }
.cover .sub::before { content: ""; display: block; width: 10mm; margin: 0 auto 3mm; border-top: 0.3mm solid var(--rose); }

.back { justify-content: flex-start; }
.back .vt { position: absolute; top: 22mm; right: 12mm; writing-mode: vertical-rl; font-family: 'Gulzar';
            font-size: 24pt; color: var(--ink); }
.back .rule { position: absolute; top: 26mm; right: 30mm; width: 0.3mm; height: 82mm; background: var(--hair); }
.back .blurb { position: absolute; top: 34mm; right: 38mm; left: 18mm; text-align: justify; font-size: 12.5pt;
               line-height: 2.1; color: var(--ink); }
.back .blurb p { margin: 0 0 4mm; }
.back .blurb .q { font-family: 'Aref Ruqaa'; font-size: 14pt; color: var(--rose); text-align: right; }
.back .mark { position: absolute; bottom: 52mm; left: 0; right: 0; font-family: 'Reem Kufi'; font-size: 8pt; color: var(--muted); }
.back .mark .a { display: block; margin-top: 1.5mm; font-family: 'Aref Ruqaa'; font-size: 12pt; color: var(--rose); }

/* ---- front matter */
.half-title h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 24pt; margin: 0; color: var(--ink); }
.title-page { justify-content: flex-start; padding-top: 30mm; }
.title-page .kicker { font-family: 'Reem Kufi'; font-size: 9.5pt; color: var(--rose); }
.title-page .lettering { margin: 6mm 0 0; transform: scale(.86); transform-origin: top center; }
.title-page .sub { font-size: 12.5pt; color: var(--muted); max-width: 92mm; line-height: 1.8; }
.title-page .author { margin-top: 5mm; font-family: 'Aref Ruqaa'; font-size: 14pt; color: var(--rose); }
.title-page .strip { position: absolute; bottom: 26mm; left: 0; right: 0; width: 110mm; }
.colophon { justify-content: flex-end; padding: 0 24mm 30mm; font-size: 8.5pt; line-height: 2; color: var(--muted); }
.colophon .t { font-family: 'Aref Ruqaa'; font-size: 12pt; color: var(--ink); }
.colophon hr { width: 14mm; border: 0; border-top: 0.3mm solid var(--hair); margin: 4mm auto; }
.dedication, .prelude { padding: 0 24mm; }
.dedication h2, .toc h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 22pt; margin: 0 0 9mm; }
.dedication .to { font-family: 'Aref Ruqaa'; font-size: 19pt; color: var(--rose); margin: 0 0 6mm; }
.dedication p { margin: 0 0 6mm; font-size: 12pt; line-height: 2; }
.dedication .who { display: block; margin: 0 auto 2.5mm; width: 2.2mm; height: 2.2mm; border-radius: 50%; }
.dedication .who.her { background: var(--rose); } .dedication .who.him { background: var(--gold); }
.dedication .strip { position: absolute; bottom: 22mm; left: 0; right: 0; width: 80mm; opacity: .9; }
.prelude p { margin: 0; font-size: 14pt; line-height: 2.2; }
.prelude p::before, .prelude p::after { color: var(--rose); font-family: 'Aref Ruqaa'; font-size: 20pt; }
.prelude p::before { content: "«"; } .prelude p::after { content: "»"; }
.toc { justify-content: flex-start; padding: 26mm 18mm 0; }
.toc h2 { margin-bottom: 8mm; }
.toc ol { list-style: none; margin: 0; padding: 0; width: 100%; }
.toc li { display: flex; align-items: baseline; gap: 2.5mm; padding: 1.15mm 0; font-size: 10.5pt; line-height: 1.55; }
.toc .num { flex: 0 0 9mm; font-family: 'Aref Ruqaa'; font-size: 13pt; color: var(--rose); text-align: right; }
.toc .dots { flex: 1; border-bottom: 0.25mm dotted #b8ab9b; transform: translateY(-1.2mm); min-width: 6mm; }
.toc .pg { color: var(--muted); font-size: 10pt; }

/* ---- chapter openers: the picture fills the page, words sit in the fog of the sky */
.opener { justify-content: flex-start; padding: 0 20mm; }
.opener .ord { margin-top: 27mm; font-family: 'Reem Kufi'; font-size: 9.5pt; color: var(--rose); }
.opener h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 25pt; line-height: 1.5; margin: 5mm 0 0; color: var(--ink); }
.opener blockquote { margin: 9mm 6mm 0; font-size: 11.5pt; line-height: 2; color: #6f675f; }
.opener blockquote::before { content: ""; display: block; width: 8mm; margin: 0 auto 4mm; border-top: 0.3mm solid var(--rose); }
.opener blockquote span { display: block; }
.opener.dark .ord { color: #d99aa3; }
.opener.dark h2 { color: #eef1f6; }
.opener.dark blockquote { color: #aab3c3; }
.opener .floating { position: absolute; left: 0; right: 0; top: 104mm; font-family: 'Aref Ruqaa'; font-size: 26pt;
                    color: var(--rose); opacity: .5; }

/* ---- chapter text */
.chapter-body { break-before: page; }
.chapter-body .head { text-align: center; margin: 2mm 0 9mm; }
.chapter-body .head .t { font-family: 'Aref Ruqaa'; font-size: 13pt; color: var(--rose); line-height: 1.6; }
.chapter-body .head .r { width: 12mm; margin: 2.5mm auto 0; border-top: 0.3mm solid var(--hair); }
.chapter-body p { margin: 0; text-indent: 1.4em; text-align: justify; widows: 2; orphans: 2; }
.chapter-body p.first { text-indent: 0; }
.chapter-body p.first::first-line { color: var(--rose); }
.chapter-body .end-mark { margin-top: 8mm; break-inside: avoid; break-before: avoid; }
.chapter-body .end-mark .strip { width: 52mm; }

/* ---- words that act out what they say */
.sp { break-inside: avoid; margin: 7mm 0; text-align: center; text-indent: 0; }
.sp p, .chapter-body .sp p { text-indent: 0; text-align: center; margin: 0; }
.echo { position: relative; font-family: 'Aref Ruqaa'; font-size: 20pt; line-height: 1.6; }
.echo .ghost { position: absolute; left: 0; right: 0; top: 0; transform: translate(-1.6mm, 1.2mm); color: var(--rose); opacity: .28; }
.echo .real { position: relative; }
.reach .a { text-align: right; font-size: 13pt; }
.reach .b { display: flex; align-items: center; gap: 2mm; font-size: 13pt; margin-top: 1mm; }
.reach .b .line { flex: 1; border-top: 0.45mm dotted var(--rose); opacity: .7; }
.reach .b .to { font-family: 'Aref Ruqaa'; font-size: 18pt; color: var(--rose); }
.pull { padding: 0 6mm; font-size: 13.5pt; line-height: 2; color: var(--ink); }
.pull::before, .pull::after { content: ""; display: block; width: 8mm; margin: 2mm auto; border-top: 0.3mm solid var(--rose); }
.rule { display: flex; align-items: center; gap: 4mm; font-family: 'Aref Ruqaa'; font-size: 16pt; }
.rule::before, .rule::after { content: ""; flex: 1; border-top: 0.3mm solid var(--hair); }
.fall { position: relative; height: 38mm; }
.fall .line { display: flex; justify-content: center; gap: 1.8mm; font-size: 12pt; white-space: nowrap; }
.fall .line span { display: inline-block; transform-origin: center bottom; }
.fall .ground { position: absolute; top: 33mm; left: 0; width: 42%; border-top: 0.4mm solid var(--ink); opacity: .3; }
.absent .s { font-size: 13pt; }
.absent svg { display: block; margin: 3mm auto 0; width: 26mm; }
.drift p { font-size: 12.5pt; line-height: 2.1; }
.drift .w { display: flex; justify-content: space-between; margin: 0 auto; }
.word-p { text-align: justify; text-indent: 0 !important; }
.word-p .bh { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 18pt; color: var(--rose); line-height: 1; }
.twotone .a { font-size: 13pt; color: var(--rose); }
.twotone .b { font-size: 13pt; color: var(--muted); }
.scatter { position: relative; height: 62mm; margin: 6mm 0 2mm; }
.scatter p { position: absolute; text-align: center !important; white-space: nowrap; }
.big { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 21pt; line-height: 1.6; }
.big-rose { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 23pt; color: var(--rose); line-height: 1.6; }
.big-gold { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 21pt; color: var(--gold); line-height: 1.6; }
.heartbeat svg { display: block; width: 100%; height: 9mm; margin-top: 2mm; }
.balance p { font-size: 13pt; }
.balance .a { text-align: right !important; }
.balance .b { text-align: left !important; }
.balance em { font-style: normal; font-family: 'Aref Ruqaa'; font-size: 16pt; }
.balance .a em { color: var(--rose); } .balance .b em { color: var(--gold); }
.stairs p { text-align: right !important; }
.stairs .s0 { font-size: 11pt; color: var(--muted); }
.stairs .s1 { font-size: 12pt; color: #6f675f; padding-right: 10mm; }
.stairs .s2 { font-size: 12pt; padding-right: 20mm; }
.stairs .s3 { font-family: 'Aref Ruqaa'; font-size: 17pt; color: var(--rose); text-align: center !important; margin-top: 3mm !important; line-height: 1.6; }
.road svg { display: block; width: 60mm; margin: 0 auto; }
.road p { font-family: 'Aref Ruqaa'; font-size: 17pt; }
.pairs .c { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 18pt; line-height: 1.5; margin-top: 4mm !important; }
.pairs .u { font-size: 11pt; color: #9b9289; padding: 0 8mm; line-height: 1.8; }
.fade p { font-size: 14pt; }
.last { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 24pt; color: var(--rose); margin-top: 12mm; }

/* ---- epilogue over its picture */
.khatima { justify-content: flex-start; padding: 26mm 22mm 0; }
.khatima h2 { font-family: 'Aref Ruqaa'; font-weight: 700; font-size: 24pt; margin: 0 0 6mm; color: var(--rose); }
.khatima p { margin: 0 0 3.5mm; font-size: 12pt; line-height: 2; color: #4f4943; }
.khatima p:last-of-type { margin-top: 5mm; font-family: 'Aref Ruqaa'; font-size: 16pt; color: var(--ink); }
"""


def page_css(book):
    """Running heads: book title on right-hand pages, chapter title on left-hand pages."""
    head = ("font-family: 'Reem Kufi'; font-size: 7.5pt; color: #9a9087; "
            "vertical-align: bottom; padding-bottom: 7mm;")
    foot = ("content: counter(page, arabic-indic); font-family: 'Amiri'; font-size: 9.5pt; "
            "color: #877e75; vertical-align: top; padding-top: 7mm;")
    rules = [
        f"@page :right {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page :left {{ @top-center {{ content: {css_str(book['title'])}; {head} }} }}",
        f"@page {{ @bottom-center {{ {foot} }} }}",
    ]
    for n, ch in enumerate(book["chapters"], 1):
        rules.append(f"@page ch{n}:left {{ @top-center {{ content: {css_str(ch['title'])}; {head} }} }}")
    return "\n".join(rules)


# ---------------------------------------------------------------- special settings

def words(text):
    return text.split(" ")


def sp_fall(text):
    """The sentence of the fall: he stands, then the words tumble down to the ground."""
    ws = words(text)
    n = len(ws)
    out = []
    for i, w in enumerate(ws):
        t = max(0, i - 1) / (n - 2)
        drop = (t ** 2.2) * 24
        rot = -t * 30 if i < n - 1 else -4
        out.append(f'<span style="transform:translateY({drop:.1f}mm) rotate({rot:.0f}deg)">{esc(w)}</span>')
    return f'<div class="sp fall"><div class="line">{"".join(out)}</div><div class="ground"></div></div>'


def sp_drift(ps):
    widths = [None, 72, 100]
    rows = []
    for p, w in zip(ps, widths):
        if w is None:
            rows.append(f"<p>{esc(p)}</p>")
        else:
            rows.append(f'<p class="w" style="width:{w}%">' + "".join(f"<span>{esc(x)}</span>" for x in words(p)) + "</p>")
    return f'<div class="sp drift">{"".join(rows)}</div>'


def sp_scatter(ps):
    # overthinking: questions crowd and overlap at different sizes and depths
    spots = [(4, 50, 15, 0.95, -2), (18, 6, 11.5, 0.7, 1.5), (31, 2, 10.5, 0.55, -1), (46, 14, 11, 0.8, 2)]
    out = []
    for p, (top, right, size, op, rot) in zip(ps, spots):
        out.append(f'<p style="top:{top}mm;right:{right}%;font-size:{size}pt;opacity:{op};'
                   f'transform:rotate({rot}deg)">{esc(p)}</p>')
    return f'<div class="sp scatter">{"".join(out)}</div>'


def sp_fade(text):
    ws = words(text)
    n = len(ws)
    spans = []
    for i, w in enumerate(ws):
        op = 1 - (i / (n - 1)) ** 1.3 * 0.85
        spans.append(f'<span style="opacity:{op:.2f}">{esc(w)}</span>')
    return f'<div class="sp fade"><p>{" ".join(spans)}</p></div>'


HEARTBEAT_SVG = ('<svg viewBox="0 0 400 30" preserveAspectRatio="none" aria-hidden="true">'
                 '<polyline fill="none" stroke="#9c4a55" stroke-width="1.2" stroke-linejoin="round" opacity=".7" '
                 'points="0,18 170,18 178,14 184,18 192,18 197,24 204,3 211,27 217,18 232,18 240,15 248,18 400,18"/></svg>')

ROAD_SVG = ('<svg viewBox="0 0 200 40" aria-hidden="true"><g fill="none" stroke="#b8ab9b" stroke-width="1">'
            '<line x1="40" y1="40" x2="98" y2="3"/><line x1="160" y1="40" x2="102" y2="3"/></g>'
            '<circle cx="100" cy="17" r="2.2" fill="#96794d"/></svg>')

ABSENT_SVG = ('<svg viewBox="0 0 100 12" aria-hidden="true"><line x1="10" y1="6" x2="90" y2="6" stroke="#cfc6ba" stroke-width="0.8"/>'
              '<circle cx="66" cy="6" r="4" fill="#96794d"/>'
              '<circle cx="34" cy="6" r="3.6" fill="none" stroke="#9c4a55" stroke-width="0.9" stroke-dasharray="1.6 1.4"/></svg>')


def render_special(kind, ps):
    if kind == "echo":
        t = esc(ps[0])
        return f'<div class="sp echo"><span class="ghost">{t}</span><span class="real">{t}</span></div>'
    if kind == "reach":
        b = ps[1].rsplit(" ", 1)
        return (f'<div class="sp reach"><p class="a">{esc(ps[0])}</p>'
                f'<div class="b"><span>{esc(b[0])}</span><span class="line"></span><span class="to">{esc(b[1])}</span></div></div>')
    if kind == "pull":
        return f'<div class="sp pull">{esc(ps[0])}</div>'
    if kind == "rule":
        return f'<div class="sp rule">{esc(ps[0])}</div>'
    if kind == "fall":
        return sp_fall(ps[0])
    if kind == "absent":
        return f'<div class="sp absent"><div class="s">{esc(ps[0])}</div>{ABSENT_SVG}</div>'
    if kind == "drift":
        return sp_drift(ps)
    if kind == "word":
        t = esc(ps[0]).replace("«بحبكِ»", '«<span class="bh">بحبكِ</span>»')
        return f'<p class="first word-p">{t}</p>'
    if kind == "twotone":
        return f'<div class="sp twotone"><p class="a">{esc(ps[0])}</p><p class="b">{esc(ps[1])}</p></div>'
    if kind == "scatter":
        return sp_scatter(ps)
    if kind in ("big", "big-rose", "big-gold"):
        return f'<div class="sp {kind}">{esc(ps[0])}</div>'
    if kind == "heartbeat":
        return f'<div class="sp heartbeat"><p>{esc(ps[0])}</p>{HEARTBEAT_SVG}</div>'
    if kind == "balance":
        a = esc(ps[0]).replace("أخسركِ", "<em>أخسركِ</em>")
        b = esc(ps[1]).replace("نفسي", "<em>نفسي</em>", 1)
        return f'<div class="sp balance"><p class="a">{a}</p><p class="b">{b}</p></div>'
    if kind == "stairs":
        return '<div class="sp stairs">' + "".join(f'<p class="s{i}">{esc(p)}</p>' for i, p in enumerate(ps)) + "</div>"
    if kind == "road":
        return f'<div class="sp road"><p>{esc(ps[0])}</p>{ROAD_SVG}</div>'
    if kind == "pairs":
        rows = "".join(f'<p class="{"c" if i % 2 == 0 else "u"}">{esc(p)}</p>' for i, p in enumerate(ps))
        return f'<div class="sp pairs">{rows}</div>'
    if kind == "fade":
        return sp_fade(ps[0])
    if kind == "last":
        return f'<div class="sp last">{esc(ps[0])}</div>'
    raise ValueError(kind)


# ---------------------------------------------------------------- pages

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


WAVE_SVG = ('<svg class="wave" viewBox="0 0 90 10" preserveAspectRatio="none" aria-hidden="true">'
            '<path d="M0 5 Q4.5 1 9 5 T18 5 T27 5 T36 5 T45 5 T54 5 T63 5 T72 5 T81 5 T90 5" fill="none" '
            'stroke="#2e2a27" stroke-width="1"/></svg>')


def lettering():
    """The title set as lettering (tuned for «ما زلتُ أختاركِ»)."""
    return f"""<div class="lettering" role="heading" aria-level="1" aria-label="ما زلتُ أختاركِ">
    <div class="big">أختـــــــاركِ</div>
    <div class="brush"></div><div class="still">ما زلتُ</div>
    {WAVE_SVG}<div class="star">✦</div>
    <div class="en">I <b>still</b><br>choose you.</div>
  </div>"""


def cover_front(book):
    return f"""
<div class="sheet art cover" style="background-image:url(art/cover.jpg)">
  <div class="side"><div class="bar"></div><div class="v">رواية</div></div>
  {lettering()}
  <div class="author">{esc(AUTHOR)}</div>
  <div class="sub">{esc(book['subtitle'])}</div>
</div>"""


def cover_back(book):
    return f"""
<div class="sheet art back" style="background-image:url(art/back.jpg)">
  <div class="vt">{esc(book['title'])}</div>
  <div class="rule"></div>
  <div class="blurb">
    <p>{esc(book['blurb'])}</p>
    <p class="q">{esc(book['khatima'][-3])}</p>
  </div>
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
  <img class="strip" src="art/strip-title.png" alt="">
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
  <div>جُمع النص بخطوط أميري، وعارف رقعة، وريم كوفي</div>
  <div>الرسوم مرسومة خصيصًا لهذه الرواية</div>
</div>""")
    ded = book["dedication"]
    b, mk = ctx.recto("DE")
    out.append(f"""{b}
<div class="sheet dedication">{mk}
  <h2>إهداء</h2>
  <div class="to">{esc(ded[0])}</div>
  <p><span class="who her"></span>{esc(ded[1])}</p>
  <p><span class="who him"></span>{esc(ded[2])}</p>
  <img class="strip" src="art/strip-dedication.png" alt="">
</div>""")
    b, mk = ctx.recto("PR")
    out.append(f"""{b}
<div class="sheet prelude">{mk}
  <p>{esc(book['blurb'])}</p>
</div>""")
    items = []
    for n, ch in enumerate(book["chapters"], 1):
        pg = ar(ctx.toc_pages.get(f"C{n:02d}", 0))
        items.append(f'<li><span class="num">{ar(n)}</span><span class="name">{esc(ch["title"])}</span>'
                     f'<span class="dots"></span><span class="pg">{pg}</span></li>')
    items.append(f'<li><span class="num">•</span><span class="name">خاتمة</span>'
                 f'<span class="dots"></span><span class="pg">{ar(ctx.toc_pages.get("KH", 0))}</span></li>')
    b, mk = ctx.recto("TO")
    out.append(f"""{b}
<div class="sheet toc">{mk}
  <h2>الفهرس</h2>
  <ol>{''.join(items)}</ol>
</div>""")
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


def chapter(n, ch, ctx):
    quote = "".join(f"<span>{esc(q)}</span>" for q in QUOTES[n])
    b, mk = ctx.recto(f"C{n:02d}")
    dark = " dark" if n in DARK_OPENERS else ""
    floating = '<div class="floating">بحبكِ</div>' if n == 7 else ""
    end = "" if n == 14 else f'<div class="end-mark"><img class="strip" src="art/end{n:02d}.png" alt=""></div>'
    return f"""
<section class="chapter">{b}
  <div class="sheet art opener{dark}" style="background-image:url(art/ch{n:02d}.jpg)">{mk}
    <div class="ord">الفصل {esc(ch['ordinal'])}</div>
    <h2>{esc(ch['title'])}</h2>
    <blockquote>{quote}</blockquote>
    {floating}
  </div>
  <div class="chapter-body" style="page: ch{n}">
    <div class="head"><div class="t">{esc(ch['title'])}</div><div class="r"></div></div>
    {chapter_paragraphs(n, ch)}
    {end}
  </div>
</section>"""


def khatima(book, ctx):
    b, mk = ctx.recto("KH")
    paras = "".join(f"<p>{esc(p)}</p>" for p in book["khatima"])
    return f"""{b}
<div class="sheet art khatima" style="background-image:url(art/khatima.jpg)">{mk}
  <h2>خاتمة</h2>
  {paras}
</div>"""


def document(book, part, ctx):
    css = FONTS_CSS + BASE_CSS
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
    print("chapter pages (print):", {k: v for k, v in sorted(print_pages.items())})


if __name__ == "__main__":
    main()
