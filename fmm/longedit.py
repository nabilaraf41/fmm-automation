"""Landscape (16:9) long-video editor: stitch the best parts of raw recordings into one YouTube/Facebook video.

    make([(file, start, end), ...], title, out_path)
Intro title card -> segments (cropped to 16:9, FMM watermark, whoosh on every cut) -> outro (follow/subscribe).
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

from fmm import sfx
from fmm.brand import base, font, label_font, LOGO, GOLD, WHITE

W, H = 1920, 1080


def card(text, sub, path):
    img, d, _ = base("event", None, (W, H))
    d = ImageDraw.Draw(img)
    d.text((W // 2, 430), text.upper(), font=font("Anton-Regular.ttf", 150), fill=GOLD, anchor="mm",
           stroke_width=6, stroke_fill=(5, 5, 5))
    d.text((W // 2, 600), sub.upper(), font=label_font(56), fill=WHITE, anchor="mm")
    img.convert("RGB").save(path)
    return path


def watermark(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 200))
    logo.thumbnail((220, 110))
    im.alpha_composite(logo, (40, 30))
    im.save(path)
    return path


def _ff(*args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-600:])


ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]


def make(segments, title, out, sub="FC MOBILE GAMEPLAY"):
    """Each piece is rendered on its own (same size, fps and audio format), then joined without re-encoding."""
    out = Path(out); tmp = out.parent / "_le"; tmp.mkdir(parents=True, exist_ok=True)
    sfx.build()
    wm = watermark(tmp / "wm.png")
    silent = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    pieces = []
    for i, (img, secs) in enumerate([(card(title, sub, tmp / "intro.png"), 3)]):
        p = tmp / "p00.mp4"
        _ff("-loop", "1", "-t", str(secs), "-i", str(img), "-i", str(sfx.OUT / "riser.wav"),
            "-filter_complex", "[0:v]scale=1920:1080,setsar=1[v];[1:a]apad[a]", "-map", "[v]", "-map", "[a]",
            "-t", str(secs), *ENC, str(p))
        pieces.append(p)
    for i, (f, a, b) in enumerate(segments, 1):
        p = tmp / f"p{i:02d}.mp4"
        _ff("-ss", str(a), "-t", str(b - a), "-i", str(f), "-i", str(wm), "-i", str(sfx.OUT / "whoosh.wav"),
            "-filter_complex", "[0:v]scale=-2:1080,crop=1920:1080,setsar=1[g];[g][1:v]overlay=0:0[v];[2:a]apad[a]",
            "-map", "[v]", "-map", "[a]", "-t", str(b - a), *ENC, str(p))
        pieces.append(p)
    p = tmp / "p99.mp4"
    _ff("-loop", "1", "-t", "4", "-i", str(card("FOLLOW FMM", "DAILY FC MOBILE • SUBSCRIBE", tmp / "outro.png")),
        *silent, "-filter_complex", "[0:v]scale=1920:1080,setsar=1[v]", "-map", "[v]", "-map", "1:a",
        "-t", "4", *ENC, str(p))
    pieces.append(p)
    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{q.resolve().as_posix()}'" + chr(10) for q in pieces), encoding="utf-8")
    _ff("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out))
    return out
