"""Compose the traced RAM mark + outlined text into final, font-free SVG lockups."""
import json, os
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out9")
FONTS = os.path.join(HERE, "fonts")
P = json.load(open(os.path.join(OUT, "paths.json")))
MX, MY = 340, 355                      # where the traced crop sits on the 1024×1536 artboard


class Face:
    def __init__(self, file):
        path = os.path.join(FONTS, file)
        self.blob = hb.Blob.from_file_path(path)
        self.face = hb.Face(self.blob)
        self.font = hb.Font(self.face)
        self.tt = TTFont(path)
        self.upem = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()

    def run(self, text, size, x, y, anchor="middle", tracking=0.0):
        """Return (svg path d, advance width) for one shaped line; tracking in em."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {})
        k = size / self.upem
        pos = list(zip(buf.glyph_infos, buf.glyph_positions))
        total = sum(p.x_advance for _, p in pos)*k + tracking*size*(len(pos) - 1)
        start = {"start": x, "middle": x - total/2, "end": x - total}[anchor]
        pen = SVGPathPen(self.gs)
        cx = 0.0
        for info, p in pos:
            name = self.order[info.codepoint]
            gx = start + (cx + p.x_offset)*k if tracking == 0 else start + cx*k + p.x_offset*k
            tp = TransformPen(pen, (k, 0, 0, -k, gx, y - p.y_offset*k))
            self.gs[name].draw(tp)
            cx += p.x_advance + (tracking*size/k if tracking else 0)
        return pen.getCommands(), total


TAJ8 = Face("Tajawal-800.ttf")
TAJ7 = Face("Tajawal-700.ttf")
RUB = Face("Rubik-700.ttf")


def lockup_text(col):
    """RAM | رام  +  subtitle, centred on x=512."""
    ar, wa = TAJ8.run("رام", 64, 0, 0)
    la, wl = RUB.run("RAM", 50, 0, 0, tracking=0.16)
    gap, bar = 26, 5
    total = wl + gap + bar + gap + wa
    x0 = 512 - total/2
    la, _ = RUB.run("RAM", 50, x0, 988, "start", tracking=0.16)
    ar, _ = TAJ8.run("رام", 64, x0 + wl + 2*gap + bar, 988, "start")
    bx = x0 + wl + gap
    sub, _ = TAJ7.run("رام للشؤون العسكرية والأمنية", 35, 512, 1050)
    return (f'<path d="{la}" fill="{col}"/><path d="{ar}" fill="{col}"/>'
            f'<rect x="{bx:.1f}" y="944" width="{bar}" height="50" rx="1.5" fill="{col}"/>'
            f'<path d="{sub}" fill="{col}"/>')


def mark(theme, uid):
    if theme == "dark":
        base, b0, b1, g0, g1 = "#FFFFFF", "#9FB8E6", "#C9D8F2", "#8FA0B8", "#C3CEDC"
    else:
        base, b0, b1, g0, g1 = "#0E2A6E", "#2C4F92", "#4468AE", "#8C98A9", "#BAC3CF"
    return (f'<defs>'
            f'<linearGradient id="band{uid}" x1="0" y1="0" x2="0.7" y2="1"><stop offset="0" stop-color="{b1}" stop-opacity="0"/>'
            f'<stop offset="0.12" stop-color="{b1}" stop-opacity="1"/><stop offset="0.85" stop-color="{b0}" stop-opacity="1"/>'
            f'<stop offset="1" stop-color="{b0}" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="grey{uid}" x1="1" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{g0}"/><stop offset="1" stop-color="{g1}"/></linearGradient>'
            f'<clipPath id="clip{uid}"><path d="{P["blue"]}" fill-rule="evenodd"/></clipPath>'
            f'<filter id="soft{uid}" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="0.8"/></filter>'
            f'</defs>'
            f'<g transform="translate({MX} {MY})">'
            f'<path d="{P["blue"]}" fill="{base}" fill-rule="evenodd"/>'
            f'<g clip-path="url(#clip{uid})"><g filter="url(#soft{uid})">' + "".join(f'<path d="M{sp}" fill="url(#band{uid})"/>' for sp in P["light"].split("M") if sp.strip()) + '</g></g>'
            f'<path d="{P["grey"]}" fill="url(#grey{uid})" fill-rule="evenodd"/>'
            f'</g>')


def doc(w, h, body, vb=None):
    vb = vb or f"0 0 {w} {h}"
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" width="{w}" height="{h}">{body}</svg>'


SILK = ('<defs><radialGradient id="bgL" cx="0.35" cy="0.3" r="0.9"><stop offset="0" stop-color="#FFFFFF"/>'
        '<stop offset="1" stop-color="#E9EBF0"/></radialGradient>'
        '<radialGradient id="bgD" cx="0.5" cy="0.35" r="0.8"><stop offset="0" stop-color="#163276"/>'
        '<stop offset="1" stop-color="#0A1A44"/></radialGradient></defs>')

files = {
    "ram-logo-light.svg": doc(1024, 1536, SILK + '<rect width="1024" height="1536" fill="url(#bgL)"/>' + mark("light", "L") + lockup_text("#11275F")),
    "ram-logo-transparent.svg": doc(1024, 1536, mark("light", "T") + lockup_text("#11275F")),
    "ram-logo-dark.svg": doc(1024, 1536, SILK + '<rect width="1024" height="1536" fill="url(#bgD)"/>' + mark("dark", "D") + lockup_text("#FFFFFF")),
    # mark only, square, tightly framed
    "ram-mark-transparent.svg": doc(1024, 1024, mark("light", "M"), vb="250 330 524 600"),
    "ram-mark-white.svg": doc(1024, 1024, '<rect x="250" y="330" width="524" height="600" fill="#FFFFFF"/>' + mark("light", "W"), vb="250 330 524 600"),
}
for name, s in files.items():
    open(os.path.join(OUT, name), "w").write(s)
print("ok")
