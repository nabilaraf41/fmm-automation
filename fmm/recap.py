"""Recap videos from our own best Reels (owner ideas 7 + 10, 11 Nov): Sunday "Top 5 of the week",
last day of the month "Best of <Month>" (top 10). Reels are downloaded back from Instagram (media_url),
put side by side on a blurred 16:9 background with a "#N" tag, and uploaded to YouTube + Facebook as a long video
(watch hours for YPP, in-stream ads on Facebook). Runs from 20:00 BDT in the hourly cloud job.
"""
import calendar, datetime as dt, json, subprocess, time
from pathlib import Path

import requests
from fmm import poster

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "content" / "recap.json"
OUT = ROOT / "output" / "recap"
FONT = ROOT / "assets" / "fonts" / "LeagueSpartan.ttf"


def due(today):
    """('week', 7, 5) on Sundays, ('month', <days>, 10) on the last day of the month, else None."""
    if today.day == calendar.monthrange(today.year, today.month)[1]:
        return "month", today.day, 10
    if today.weekday() == 6:
        return "week", 7, 5
    return None


def best_reels(days, n):
    from fmm import growth
    since = (dt.datetime.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    rows, seen = [], set()
    for e in log:
        ig = str(e.get("instagram") or "")
        if e.get("kind") != "reel" or e.get("at", "") < since or not ig.isdigit() or "trial" in str(e.get("type")) \
                or e.get("type") in ("long", "evergreen", "code_reel") or ig in seen:
            continue
        seen.add(ig)
        rows.append((growth.score(growth.metrics(e)), e))
    rows.sort(key=lambda r: -r[0])
    return [e for _, e in rows[:n]]


def clip(e, i, total):
    """Reel -> 1920x1080 segment: blurred fill + sharp vertical video centred + '#rank' badge."""
    url = poster.call("GET", e["instagram"], params={"fields": "media_url"})["media_url"]
    src = OUT / f"src_{i}.mp4"
    src.write_bytes(requests.get(url, timeout=300).content)
    out = OUT / f"seg_{i}.mp4"
    rank = total - i  # countdown: worst of the top first, #1 last
    vf = (f"[0:v]split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=30:5[bg];"
          f"[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0,"
          f"drawtext=fontfile='{FONT.as_posix().replace(':', chr(92) + ':')}':text='#{rank}':fontsize=160:"
          f"fontcolor=yellow:borderw=10:bordercolor=black:x=80:y=60,fps=30,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", vf, "-map", "[v]", "-map", "0:a?", "-map", "1:a", "-shortest",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ar", "44100", "-ac", "2",
                    str(out)], check=True)
    return out


def build(reels):
    OUT.mkdir(parents=True, exist_ok=True)
    segs = [clip(e, i, len(reels)) for i, e in enumerate(reversed(reels))]
    lst = OUT / "list.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    out = OUT / "recap.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-ac", "2", str(out)], check=True)
    return out


def run():
    now = dt.datetime.now()  # cloud runner TZ = Asia/Dhaka
    d = due(now.date())
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    key = now.date().isoformat()
    if not d or now.hour < 20 or st.get(key):
        return None
    kind, days, n = d
    reels = best_reels(days, n)
    if len(reels) < 3:
        return None
    mp4 = build(reels)
    title = (f"Top {len(reels)} FC Mobile Moments This Week 🔥 - FC Mobile" if kind == "week"
             else f"Best of FMM {now.strftime('%B')}: Top {len(reels)} FC Mobile Posts 🔥 - FC Mobile")
    nl = "\n"
    cap = (f"{title}{nl}{nl}Our most-watched FC Mobile posts, counted down to #1. Which one was your favourite? 👇{nl}{nl}"
           f"🔔 Subscribe for daily FC Mobile cards, Top 10 lists and codes{nl}"
           f"📸 Instagram: https://www.instagram.com/fc_fmm/{nl}{nl}#FCMobile #FIFAMobile #EAFC #FMM")
    from fmm import thumb
    frame = OUT / "frame.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-3", "-i", str(mp4), "-frames:v", "1", str(frame)])
    cover = thumb.cover_wide(frame, f"TOP {len(reels)}", OUT / "recap_cover.jpg", face=thumb.face_for(now.day))
    res = {}
    try:
        from fmm import youtube
        res["youtube"] = youtube.upload(mp4, cap, short=False)[0]
    except Exception as ex:
        print("recap youtube failed:", str(ex)[:150])
    try:
        res["facebook"] = poster.fb_video(mp4, cap.replace("Subscribe", "Follow"))
        poster.fb_thumbnail(res["facebook"], cover)
    except Exception as ex:
        print("recap facebook failed:", str(ex)[:150])
    if res:
        poster.log({"kind": "long", "file": str(mp4), "type": f"recap_{kind}", **res})
        st[key] = res
        STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    assert due(dt.date(2026, 11, 15)) == ("week", 7, 5) and due(dt.date(2026, 11, 30))[0] == "month"
    assert due(dt.date(2026, 11, 12)) is None
    print("ok")
