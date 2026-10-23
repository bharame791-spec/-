#!/usr/bin/env python3
"""Makes the trailer: art layers, a score timed to the voice-over, the animated frames, the mix.

The timeline below comes from the voice-over's pauses (ffmpeg silencedetect at -45 dB):
each entry is where a phrase starts and ends in voiceover.mp3, in seconds.

Writes video/trailer.mp4 (1920x1080, 30 fps). Usage: python3 video/make.py [--preview SECONDS] [--mix-only]
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
sys.path.insert(0, str(HERE))
import music  # noqa: E402

OFFSET = 1.5    # the voice starts after a breath of fog and music
LENGTH = 66.5   # the title holds for a few seconds after the last word

# phrase timings in the voice-over (seconds)
VO = {
    "L1": (0.00, 1.16), "L2a": (2.40, 2.97), "L2b": (3.30, 4.23),
    "L3a": (5.90, 7.24), "L3b": (7.55, 9.94), "L4": (10.88, 12.11),
    "L5a": (13.77, 14.61), "L5b": (14.92, 16.88), "L6": (18.85, 20.59),
    "L7a": (21.54, 22.67), "L7b": (23.17, 23.91), "L8": (25.76, 26.27),
    "L9a": (27.14, 28.87), "L9b": (28.87, 30.32),
    "Q1": (31.59, 31.98), "Q2": (32.38, 33.49), "Q3": (33.83, 35.54),
    "L11a": (36.36, 36.86), "L11b": (37.24, 37.71), "L12": (40.08, 41.14),
    "L13a": (42.47, 43.55), "L13b": (45.11, 46.39), "L14": (48.35, 49.82),
    "L15a": (51.81, 52.98), "L15b": (53.33, 53.88), "L16a": (56.67, 57.18), "L16b": (57.51, 58.08),
}


def v(key, end=False):
    return round(VO[key][1 if end else 0] + OFFSET, 3)


SCENES = {
    "open": 0, "near": v("L3a"), "home": v("L5a"), "pre": v("L6"), "ice": v("L7a"), "impact": v("L7b"),
    "shock": v("L7b"), "mark": v("L8"), "questions": v("Q1"), "confess": v("L12"), "open_end": v("L14"),
    "title": v("L16a"), "choose": v("L16b"), "echo": v("L4"),
}

# Each phrase is cut into chunks of two or three words ("|"), painted on one after another.
# Options: emph = indexes of chunks set on the rose brush; cls = classes for every chunk;
# x = horizontal offset in px; kind="fall" for the words that drop; shake for restless thoughts.
PHRASES = [
    ("L1", "لم أكنْ | أبحثُ عنكِ."),
    ("L2a", "كلُّ ما | في الأمر..."),
    ("L2b", "أنني تعرّفتُ إليكِ.", {"emph": [0]}),
    ("L3a", "حديثٌ بدأ | من شاشةٍ صغيرة،"),
    ("L3b", "ووصل إلى أماكن | في داخلي، | لم يصلْ | إليها أحد."),
    ("L4", "كان فيكِ | شيءٌ يُشبهني.", {"emph": [1]}),
    ("L5a", "وصارَ الحديثُ بيتًا...", {"emph": [0]}),
    ("L5b", "أعودُ إليه، | كلّما ثقُلَ العالمُ | على صدري."),
    ("L6", "ثم جاءت الكلمة... | التي لم أتوقّعها.", {"cls": "soft"}),
    ("L7a", "كنتُ واقفًا... | وفجأة،"),
    ("L7b", "وجدتُ نفسي على الأرض.", {"kind": "fall", "fall": 300}),
    ("L8", "تصالحنا.", {"emph": [0]}),
    ("L9a", "لكنّ بعضَ المواقف | تتركُ فينا أثرًا،"),
    ("L9b", "لا يختفي | بمجرّد أن نتصالح."),
    ("Q1", "هل قصّرت؟", {"emph": [0], "cls": "night", "x": 260, "shake": True}),
    ("Q2", "هل كان بإمكاني | أن أجدَ وقتًا؟", {"cls": "night", "x": -240, "shake": True}),
    ("Q3", "هل كان عليَّ | أن أتصرّفَ | بطريقةٍ مختلفة؟", {"cls": "night", "x": 140, "shake": True}),
    ("L11a", "هل ترينَني...", {"cls": "night"}),
    ("L11b", "حين أتعب؟", {"emph": [0], "cls": "night"}),
    ("L12", "أنا لا أريدُ | أن أخسرَكِ.", {"emph": [1], "x": 200}),
    ("L13a", "ولا أريدُ | أن أخسرَ نفسي...", {"x": -200}),
    ("L13b", "وأنا أحاولُ | ألّا أخسرَكِ.", {"emph": [1]}),
    ("L14", "لا أعرفُ | ماذا سيحدثُ | لهذا الحب.", {"cls": "soft"}),
    ("L15a", "لكنّني، | يا شهد..."),
    ("L15b", "ما زلتُ هنا.", {"emph": [0], "cls": "big"}),
]
TOP = 200          # the words sit in the fog of the sky
HOLD = 3.2         # longest a chunk lingers after its phrase is spoken
LEAVE = 0.35       # how long the dissolve takes


def chunks():
    out = []
    for entry in PHRASES:
        key, text, opts = entry[0], entry[1], (entry[2] if len(entry) > 2 else {})
        parts = [p.strip() for p in text.split("|")]
        counts = [len(p.split()) for p in parts]
        start, end = v(key), v(key, True)
        done = 0
        for i, part in enumerate(parts):
            c0 = start + (end - start) * done / sum(counts)
            done += counts[i]
            c1 = start + (end - start) * done / sum(counts)
            cls = " ".join(filter(None, [opts.get("cls", ""), "emph" if i in opts.get("emph", []) else ""]))
            out.append({"text": part, "start": round(c0, 3), "spoken": round(c1, 3), "phraseEnd": end,
                        "paint": round(min(0.55, max(0.3, 0.7 * (c1 - c0))), 3), "leave": LEAVE,
                        "top": TOP, "cls": cls, "x": opts.get("x", 0), "shake": opts.get("shake", False),
                        "kind": opts.get("kind", ""), "fall": opts.get("fall", 0)})
    # each chunk dissolves as the next is painted (or after lingering a while in a long silence)
    for c, nxt in zip(out, out[1:] + [None]):
        until = nxt["start"] + 0.12 if nxt else SCENES["title"]
        c["out"] = round(min(until, c["phraseEnd"] + HOLD), 3)
    return out


def run(*cmd):
    subprocess.run(list(map(str, cmd)), check=True)


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = float(sys.argv[sys.argv.index("--preview") + 1])
    BUILD.mkdir(exist_ok=True)
    if not (BUILD / "art" / "layout.json").exists():
        run(sys.executable, HERE / "scenes.py")
    if not (BUILD / "art" / "sweep.png").exists():
        run(sys.executable, HERE / "textfx.py")

    # the score, on the same timeline as the pictures
    music.SCENES = {k: SCENES[k] for k in ("open", "near", "home", "pre", "shock", "mark", "questions",
                                           "confess", "open_end", "title")}
    music.LENGTH = LENGTH
    score = BUILD / "score.wav"
    music.write_wav(score, music.compose())

    timeline = {"t": SCENES, "length": LENGTH, "heartbeats": music.heartbeat_times(), "chunks": chunks()}
    page = (HERE / "trailer.html").read_text(encoding="utf-8")
    page = page.replace("/*TIMELINE*/", json.dumps(timeline, ensure_ascii=False))
    page = page.replace("/*LAYOUT*/", (BUILD / "art" / "layout.json").read_text())
    src = HERE / "_render.html"   # beside trailer.html so its relative paths hold
    src.write_text(page, encoding="utf-8")

    seconds = preview or LENGTH
    silent = BUILD / "picture.mp4"
    if "--mix-only" not in sys.argv:
        run("node", HERE / "render_video.js", src, silent, seconds, 30)
    src.unlink()

    # voice over the score: the music steps back under the voice
    out = HERE / ("trailer-preview.mp4" if preview else "trailer.mp4")
    delay = int(OFFSET * 1000)
    graph = (f"[1:a]adelay={delay}|{delay},aformat=channel_layouts=stereo,apad=whole_dur={LENGTH},asplit=2[vo][key];"
             "[0:a]volume=0.45[mu];"
             "[mu][key]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=500[duck];"
             "[duck][vo]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    run("ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", score, "-i", HERE / "voiceover.mp3", "-i", silent,
        "-filter_complex", graph, "-map", "2:v", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k",
        "-shortest", out)
    print("wrote", out)


if __name__ == "__main__":
    main()
