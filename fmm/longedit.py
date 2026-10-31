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


def make(segments, title, out, sub="FC MOBILE GAMEPLAY"):
    out = Path(out); tmp = out.parent / "_le"; tmp.mkdir(parents=True, exist_ok=True)
    sfx.build()
    intro, outro = card(title, sub, tmp / "intro.png"), card("FOLLOW FMM", "DAILY FC MOBILE • SUBSCRIBE", tmp / "outro.png")
    wm = watermark(tmp / "wm.png")
    inputs, parts, t = [], [], 0.0
    cuts = []
    inputs += ["-loop", "1", "-t", "3", "-i", str(intro)]
    parts.append("[0:v]scale=1920:1080,setsar=1,fps=30,format=yuv420p[p0]"); t += 3
    for i, (f, a, b) in enumerate(segments, 1):
        inputs += ["-ss", str(a), "-t", str(b - a), "-i", str(f)]
        parts.append(f"[{i}:v]scale=-2:1080,crop=1920:1080,setsar=1,fps=30,format=yuv420p[p{i}]")
        cuts.append(t); t += b - a
    k = len(segments) + 1
    inputs += ["-loop", "1", "-t", "4", "-i", str(outro), "-i", str(wm), "-i", str(sfx.OUT / "whoosh.wav")]
    parts.append(f"[{k}:v]scale=1920:1080,setsar=1,fps=30,format=yuv420p[p{k}]")
    cuts.append(t); t += 4
    chain = "".join(f"[p{i}]" for i in range(k + 1)) + f"concat=n={k + 1}:v=1:a=0[cat]"
    wm_i, wh_i = k + 1, k + 2
    vids = f"[cat][{wm_i}:v]overlay=0:0:enable='between(t,3,{t - 4:.2f})'[v]"
    aud = ";".join(f"[{wh_i}:a]adelay={int(c * 1000)}|{int(c * 1000)}[w{j}]" for j, c in enumerate(cuts))
    mix = "".join(f"[w{j}]" for j in range(len(cuts))) + f"amix=inputs={len(cuts)}:normalize=0,apad,atrim=0:{t:.2f},loudnorm=I=-14:TP=-1.5[a]"
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(parts) + ";" + chain + ";" + vids
                        + ";" + aud + ";" + mix, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
                        "-crf", "21", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)],
                       capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-600:])
    return out
