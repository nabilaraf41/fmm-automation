"""Landscape gameplay (goal clips or full matches) -> vertical FMM Reels.

    python -m fmm.clips peaks <video>                 -> highlight times (loudest moments: goals, crowd, commentary)
    python -m fmm.clips make <video> [title] [index]  -> output/clips/<name>_<i>.mp4 (+ _cover.jpg)

Layout: blurred zoomed copy fills 9:16, the gameplay sits in the middle slightly zoomed, big title on top,
FMM bar at the bottom. Effects: punch-in on the highlight, 0.5x slow-motion replay of the moment,
whoosh + impact sound on top of the game audio.
"""
import json, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "clips"
RW, RH = 1080, 1920


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")


def duration(video):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)])
    return float(r.stdout.strip() or 0)


def loudness(video, step=0.5):
    """RMS loudness (dB) per `step` seconds, smoothed over ~1.5 s so a goal roar beats a single kick."""
    n = int(44100 * step)
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vn", "-af",
             f"aresample=44100,asetnsamples=n={n}:p=0,astats=metadata=1:reset=1,"
             "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-", "-f", "null", "-"])
    ts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stdout)]
    db = [float(x) if x not in ("-inf", "inf") else -120.0
          for x in re.findall(r"RMS_level=(-?inf|-?[\d.]+)", r.stdout)]
    raw = list(zip(ts, db))
    k = 1  # neighbours each side
    return [(t, sum(v for _, v in raw[max(0, i - k):i + k + 1]) / len(raw[max(0, i - k):i + k + 1]))
            for i, (t, _) in enumerate(raw)]


def peaks(video, n=None, min_gap=25.0, pre=8.0, post=4.0):
    """Top-n loudest moments, at least min_gap seconds apart -> [(start, peak, end)].
    Long videos give more Reels: about one highlight per 75 s of footage (3 to 15)."""
    dur = duration(video)
    n = n or max(3, min(15, int(dur // 75)))
    if dur <= 40:  # already a short goal clip: use all of it, peak at its loudest point
        lv = loudness(video) or [(dur * 0.6, 0)]
        pk = max(lv, key=lambda x: x[1])[0]
        return [(0.0, min(pk, dur - 0.5), dur)]
    lv = loudness(video)
    if not lv:
        return [(max(0, dur / 2 - pre), dur / 2, min(dur, dur / 2 + post))]
    picked = []
    for t, s in sorted(lv, key=lambda x: -x[1]):
        if t < pre or t > dur - 1:
            continue
        if all(abs(t - p) >= min_gap for p in picked):
            picked.append(t)
        if len(picked) >= n:
            break
    return [(max(0.0, p - pre), p, min(dur, p + post)) for p in sorted(picked)]


def overlay_png(title, sub, path, card=None):
    """Transparent 1080x1920 layer: big title (top), scorer's card (lower right), FMM bar (bottom)."""
    from fmm.brand import font, LOGO, load_card
    from fmm.thumb import big_text
    im = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    if title:
        t = big_text(title.upper(), 150, (255, 230, 0), stroke=12)
        im.alpha_composite(t, ((RW - t.width) // 2, 230))
    if card:
        c = load_card(card)
        c.thumbnail((330, 460), Image.LANCZOS)
        glow = Image.new("RGBA", (c.width + 60, c.height + 60), (0, 0, 0, 0))
        glow.paste(Image.new("RGBA", c.size, (255, 215, 0, 200)), (30, 30), c)
        glow = glow.filter(ImageFilter.GaussianBlur(14))
        x, y = RW - c.width - 40, RH - 240 - c.height - 20
        im.alpha_composite(glow, (x - 30, y - 30))
        im.alpha_composite(c, (x, y))
    d = ImageDraw.Draw(im)
    d.rectangle((0, RH - 230, RW, RH - 120), fill=(5, 5, 5, 200))
    d.rectangle((0, RH - 230, RW, RH - 222), fill=(225, 6, 44, 255))
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255))
    logo.thumbnail((180, 90))
    im.alpha_composite(logo, (40, RH - 220))
    d.text((RW - 40, RH - 175), (sub or "FOLLOW FOR DAILY FC MOBILE").upper(), font=font("Poppins-SemiBold.ttf", 38),
           fill=(255, 255, 255), anchor="rm")
    im.save(path)
    return path


def make(video, title="WHAT A GOAL!!", index=0, sub=None, music=None, card=None):
    """card = the scorer's card image: shown in the Reel and as the cover's subject."""
    from fmm import sfx
    video = Path(video)
    OUT.mkdir(parents=True, exist_ok=True)
    pk = peaks(video)
    if index >= len(pk):
        return None
    start, peak, end = pk[index]
    name = f"{video.stem}_{index}"
    out = OUT / f"{name}.mp4"
    ov = overlay_png(title, sub, OUT / f"{name}_ov.png", card)
    rel = peak - start            # highlight time inside the clip
    slow_a, slow_b = max(0.0, rel - 1.5), rel + 0.8
    clip_len = end - start
    # video graph: blurred bg + centred gameplay with a punch-in around the highlight, then a 0.5x replay
    fg_zoom = f"scale=1560:-2,crop=1080:ih:(iw-1080)/2:0"
    vf = (
        f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,split=2[a][b];"
        f"[a]scale=-2:{RH},crop={RW}:{RH},boxblur=25:2,eq=brightness=-0.12:saturation=1.3[bg];"
        f"[b]{fg_zoom},scale='if(between(t,{rel - 0.4},{rel + 1.2}),1300,1080)':-2:eval=frame,"
        f"crop=1080:ih*1080/iw:(iw-1080)/2:(ih-ih*1080/iw)/2[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2-40[base];"
        f"[base][1:v]overlay=0:0,format=yuv420p[main];"
        f"[0:v]trim=start={start + slow_a}:end={start + slow_b},setpts=2*(PTS-STARTPTS),split=2[c][d];"
        f"[c]scale=-2:{RH},crop={RW}:{RH},boxblur=25:2,eq=brightness=-0.12:saturation=1.3[bg2];"
        f"[d]scale=1900:-2,crop=1080:ih:(iw-1080)/2:0[fg2];"
        f"[bg2][fg2]overlay=(W-w)/2:(H-h)/2-40[base2];"
        f"[base2][2:v]overlay=0:0,format=yuv420p[replay];"
        f"[main][replay]concat=n=2:v=1:a=0[v]"
    )
    replay_png = overlay_png("REPLAY", sub, OUT / f"{name}_ov2.png", card)
    # audio: game audio (+ slowed replay audio) with whoosh at start and impact on the goal
    sfx.build() if not (sfx.OUT / "impact.wav").exists() else None
    af = (
        f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS[ga];"
        f"[0:a]atrim=start={start + slow_a}:end={start + slow_b},asetpts=PTS-STARTPTS,atempo=0.5,volume=0.8[ra];"
        f"[ga][ra]concat=n=2:v=0:a=1[game];"
        f"[3:a]adelay=0|0[w];[4:a]adelay={int(rel * 1000)}|{int(rel * 1000)},volume=1.2[i];"
        f"[game][w][i]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]"
    )
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(ov), "-i", str(replay_png),
           "-i", str(sfx.OUT / "whoosh.wav"), "-i", str(sfx.OUT / "impact.wav"),
           "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]",
           "-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", str(out)]
    r = run(cmd)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])
    # cover: frame at the highlight, MrBeast style
    frame = OUT / f"{name}_frame.png"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(peak), "-i", str(video), "-frames:v", "1",
         "-vf", "crop=ih*3/4:ih:(iw-ih*3/4)/2:0", str(frame)])  # portrait crop of the action for the cover
    from fmm import thumb
    thumb.cover(card or (str(frame) if frame.exists() else None), title, OUT / f"{name}_cover.jpg", sub=sub,
                color="red", bg=str(frame) if (card and frame.exists()) else None)
    for tmp in (ov, replay_png, frame):
        Path(tmp).unlink(missing_ok=True)
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "peaks":
        print(json.dumps(peaks(a[1]), indent=1))
    else:
        print(make(a[1], a[2] if len(a) > 2 else "WHAT A GOAL!!", int(a[3]) if len(a) > 3 else 0))
