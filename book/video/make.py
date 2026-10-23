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

NIGHT = "night"


def line(key, text, top, out, size=None, cls="", **extra):
    css = {"top": f"{top}px"}
    if size:
        css["fontSize"] = f"{size}px"
    css.update(extra.pop("css", {}))
    return {"text": text, "start": v(key), "end": v(key, True), "out": out, "cls": cls, "css": css, **extra}


def lines():
    t = SCENES
    q_out = v("L11a") - 0.65
    return [
        line("L1", "لم أكن أبحث عنكِ.", 200, v("L2a") - 0.65),
        line("L2a", "كلُّ ما في الأمر...", 170, t["near"] - 0.65),
        line("L2b", "أنني تعرّفتُ إليكِ.", 250, t["near"] - 0.65, 60, "ruqaa rose"),
        line("L3a", "حديثٌ بدأ من شاشةٍ صغيرة،", 170, t["echo"] - 0.65),
        line("L3b", "ووصل إلى أماكن في داخلي، لم يصل إليها أحد.", 250, t["echo"] - 0.65, 44),
        line("L4", "كان فيكِ شيءٌ يُشبهني.", 200, t["home"] - 0.65, 72, "ruqaa", id="echoGhost", alpha=0.3),
        line("L4", "كان فيكِ شيءٌ يُشبهني.", 200, t["home"] - 0.65, 72, "ruqaa"),
        line("L5a", "وصار الحديثُ بيتًا...", 170, t["pre"] - 0.65),
        line("L5b", "أعودُ إليه، كلّما ثقُلَ العالمُ على صدري.", 250, t["pre"] - 0.65, 44),
        line("L6", "ثم جاءت الكلمة... التي لم أتوقّعها.", 200, t["ice"] - 0.65, css={"color": "#4a443f"}),
        line("L7a", "كنتُ واقفًا... وفجأة،", 200, t["impact"] - 0.6),
        line("L7b", "وجدتُ نفسي على الأرض.", 200, t["mark"] - 0.65, 56, kind="fall", fall=330),
        line("L8", "تصالحنا.", 200, v("L9a") - 0.65, 52, "ruqaa"),
        line("L9a", "لكنّ بعضَ المواقف تتركُ فينا أثرًا،", 170, t["questions"] - 0.65),
        line("L9b", "لا يختفي بمجرّد أن نتصالح.", 250, t["questions"] - 0.65, 46),
        line("Q1", "هل قصّرت؟", 120, q_out, 66, f"ruqaa {NIGHT}", kind="dim", dimAt=v("Q2"), drift=True,
             css={"left": "auto", "right": "13%"}),
        line("Q2", "هل كان بإمكاني أن أجدَ وقتًا؟", 250, q_out, 44, NIGHT, kind="dim", dimAt=v("Q3"), drift=True,
             css={"right": "auto", "left": "9%"}),
        line("Q3", "هل كان عليَّ أن أتصرّفَ بطريقةٍ مختلفة؟", 380, q_out, 40, NIGHT, drift=True),
        line("L11a", "هل ترينَني...", 200, t["confess"] - 0.65, 70, f"ruqaa {NIGHT}"),
        line("L11b", "حين أتعب؟", 300, t["confess"] - 0.65, 50, NIGHT),
        line("L12", "أنا لا أريدُ أن أخسرَكِ.", 160, t["open_end"] - 0.5, 50, color={"أخسرَكِ": "rose"},
             css={"left": "auto", "right": "12%"}),
        line("L13a", "ولا أريدُ أن أخسرَ نفسي...", 270, t["open_end"] - 0.5, 50, color={"نفسي": "gold"},
             css={"right": "auto", "left": "12%"}),
        line("L13b", "وأنا أحاولُ ألّا أخسرَكِ.", 390, t["open_end"] - 0.5, 50, color={"أخسرَكِ": "rose"}),
        line("L14", "لا أعرفُ ماذا سيحدثُ لهذا الحب.", 200, v("L15a") - 0.65, css={"color": "#5a534c"}),
        line("L15a", "لكنّني، يا شهد...", 175, t["title"] - 0.5),
        line("L15b", "ما زلتُ هنا.", 265, t["title"] - 0.5, 80, "ruqaa rose"),
    ]


def run(*cmd):
    subprocess.run(list(map(str, cmd)), check=True)


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = float(sys.argv[sys.argv.index("--preview") + 1])
    BUILD.mkdir(exist_ok=True)
    if not (BUILD / "art" / "layout.json").exists():
        run(sys.executable, HERE / "scenes.py")

    # the score, on the same timeline as the pictures
    music.SCENES = {k: SCENES[k] for k in ("open", "near", "home", "pre", "shock", "mark", "questions",
                                           "confess", "open_end", "title")}
    music.LENGTH = LENGTH
    score = BUILD / "score.wav"
    music.write_wav(score, music.compose())

    timeline = {"t": SCENES, "length": LENGTH, "heartbeats": music.heartbeat_times(), "lines": lines()}
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
