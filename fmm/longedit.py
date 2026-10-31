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


PIECE = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]
FADES = ["slideleft", "wipeleft", "circleopen", "smoothleft", "zoomin", "slideright"]
T = 0.5  # transition length (s)


def label_png(text, path):
    """'GOAL 2/4' tag, top right, FMM red."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = font("Anton-Regular.ttf", 64)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle((W - tw - 110, 40, W - 40, 130), 20, fill=(225, 6, 44, 235))
    d.text((W - 75, 85), text, font=f, fill=(255, 255, 255), anchor="rm")
    im.save(path)
    return path


def make(segments, title, out, sub="FC MOBILE GAMEPLAY"):
    """segments: (file, start, end) or (file, start, end, label). Pieces render in parallel (fast preset),
    then one pass joins them with animated transitions (xfade) and a whoosh on each transition."""
    from concurrent.futures import ThreadPoolExecutor
    out = Path(out); tmp = out.parent / "_le"; tmp.mkdir(parents=True, exist_ok=True)
    sfx.build()
    wm = watermark(tmp / "wm.png")
    jobs = []
    p = tmp / "p00.mp4"
    jobs.append((p, 3, ["-loop", "1", "-t", "3", "-i", str(card(title, sub, tmp / "intro.png")), "-i", str(sfx.OUT / "riser.wav"),
                        "-filter_complex", "[0:v]scale=1920:1080,setsar=1[v];[1:a]apad[a]", "-map", "[v]", "-map", "[a]",
                        "-t", "3", *PIECE, str(p)]))
    for i, seg in enumerate(segments, 1):
        f, a, b = seg[:3]
        lab = label_png(seg[3], tmp / f"l{i}.png") if len(seg) > 3 else wm
        p = tmp / f"p{i:02d}.mp4"
        jobs.append((p, b - a, ["-ss", str(a), "-t", str(b - a), "-i", str(f), "-i", str(wm), "-i", str(lab),
                                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
                                "[0:v]scale=-2:1080:flags=fast_bilinear,crop=1920:1080,setsar=1[g];[g][1:v]overlay[w];"
                                "[w][2:v]overlay[v]", "-map", "[v]", "-map", "3:a", "-t", str(b - a), *PIECE, str(p)]))
    p = tmp / "p99.mp4"
    jobs.append((p, 4, ["-loop", "1", "-t", "4", "-i", str(card("FOLLOW FMM", "DAILY FC MOBILE • SUBSCRIBE", tmp / "outro.png")),
                        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex", "[0:v]scale=1920:1080,setsar=1[v]",
                        "-map", "[v]", "-map", "1:a", "-t", "4", *PIECE, str(p)]))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda j: _ff(*j[2]), jobs))
    # join with transitions: offset of each xfade = running length - T
    ins, fc, durs = [], [], [j[1] for j in jobs]
    for j in jobs:
        ins += ["-i", str(j[0])]
    ins += ["-i", str(sfx.OUT / "whoosh.wav")]
    v, a, run = "0:v", "0:a", durs[0]
    for k in range(1, len(jobs)):
        off = run - T
        fc.append(f"[{v}][{k}:v]xfade=transition={FADES[k % len(FADES)]}:duration={T}:offset={off:.3f}[v{k}]")
        fc.append(f"[{a}][{k}:a]acrossfade=d={T}[a{k}]")
        v, a, run = f"v{k}", f"a{k}", run + durs[k] - T
    ws = len(jobs)
    marks = [sum(durs[:k]) - k * T for k in range(1, len(jobs))]
    fc.append(f"[{ws}:a]asplit={len(marks)}" + "".join(f"[s{m}]" for m in range(len(marks))))
    fc += [f"[s{m}]adelay={int(t * 1000)}|{int(t * 1000)}[d{m}]" for m, t in enumerate(marks)]
    fc.append(f"[{a}]" + "".join(f"[d{m}]" for m in range(len(marks))) +
              f"amix=inputs={len(marks) + 1}:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[aout]")
    _ff(*ins, "-filter_complex", ";".join(fc), "-map", f"[{v}]", "-map", "[aout]", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart", str(out))
    return out
