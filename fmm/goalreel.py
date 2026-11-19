"""Goal Reels from H2H footage, built on the PC from goals the OWNER confirmed (no guessing the scorer).

Owner rules (15-16 Nov): never title a gameplay Reel with a player unless that player's goals are verified; length from
the top-creator study: multi-goal story ~25-35 s (best ~10 s per goal: build-up -> finish). Reels land in
assets/goal_reels/ (mp4 + _cover.jpg + .txt caption); the cloud posts one per day (post_due), never the PC.
    python -m fmm.goalreel make   -> builds every job in JOBS that has no mp4 yet
"""
import datetime as dt, json, subprocess, sys
from pathlib import Path

from fmm.clips import LOOK, RH, RW, overlay_png

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "assets" / "goal_reels"

# Ronaldinho hat-trick (match 4-1, 8' 12' 30'): owner confirmed replays 1-3 = his goals (4 = assist), 16 Nov.
# (source video, start s, end s) = the last ~11 s of the best camera angle of each goal replay.
JOBS = [{
    "name": "ronaldinho_hattrick",
    "source": "output/inbox/1CIeHvazDcGTilflZ7aGcUA3NtyKR2HAm.mp4",
    "parts": [(19.5, 30.5, "GOAL 1 • 8'"), (50.5, 61.5, "GOAL 2 • 12'"), (74.5, 85.5, "GOAL 3 • 30'")],
    "title": "RONALDINHO HAT-TRICK!!",
    "card": "assets/cards/rz/f30922854.png",
    "caption": "124 Ronaldinho Hat-trick 🔥🇧🇷\n\nThree goals in one H2H match: 8', 12', 30'. Which one was the best? 👇"
               "\n\n#FCMobile #FIFAMobile #EAFC #Ronaldinho #FMM",
}]


def make(job):
    DIR.mkdir(parents=True, exist_ok=True)
    out = DIR / f"{job['name']}.mp4"
    src = ROOT / job["source"]
    segs = []
    for i, (a, b, label) in enumerate(job["parts"]):
        ov = overlay_png(job["title"], label, DIR / f"_ov{i}.png", ROOT / job["card"], title_y=430)  # below ATB box
        seg = DIR / f"_seg{i}.mp4"
        vf = (f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,split=2[x][y];"
              f"[x]scale=-2:{RH},crop={RW}:{RH},boxblur=25:2,eq=brightness=-0.12:saturation=1.3[bg];"
              f"[y]scale=1560:-2,crop=1080:ih:(iw-1080)/2:0,{LOOK}[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2-40[base];[base][1:v]overlay=0:0,format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(ov), "-filter_complex", vf, "-map", "[v]",
                        "-r", "30", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19", str(seg)], check=True)
        segs.append(seg)
        ov.unlink()
    lst = DIR / "_list.txt"
    lst.write_text("".join(f"file '{s.as_posix()}'\n" for s in segs), encoding="utf-8")
    joined = DIR / "_joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)],
                   check=True)
    # sound: the recording is silent -> library music + an impact on every goal (end of each part)
    from fmm import music, sfx, atb
    sfx.build() if not (sfx.OUT / "impact.wav").exists() else None
    track, start = music.pick(job["name"])
    total = sum(b - a for a, b, _ in job["parts"])
    hits, t = [], 0.0
    for a, b, _ in job["parts"]:
        t += b - a
        hits.append(int((t - 1.5) * 1000))
    ins = ["-i", str(joined), "-stream_loop", "-1", "-ss", str(start), "-i", track]
    af = f"[1:a]volume=0.45,afade=t=out:st={total - 1.5}:d=1.5[m]"
    for k, ms in enumerate(hits):
        ins += ["-i", str(sfx.OUT / "impact.wav")]
        af += f";[{k + 2}:a]adelay={ms}|{ms},volume=1.1[h{k}]"
    af += ";[m]" + "".join(f"[h{k}]" for k in range(len(hits))) + \
          f"amix=inputs={len(hits) + 1}:duration=first:normalize=0,alimiter=limit=0.95[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", af, "-map", "0:v", "-map", "[a]",
                    "-t", f"{total:.2f}", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                    str(out)], check=True)
    atb.box(out, job["name"], voice="goal")  # owner rule: ATB in every Reel, with a goal line in his voice
    from fmm import thumb
    frame = DIR / "_frame.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(job["parts"][-1][1] - 1.5), "-i", str(src), "-frames:v", "1",
                    "-vf", "crop=ih*3/4:ih:(iw-ih*3/4)/2:0", str(frame)], check=True)
    thumb.cover(str(ROOT / job["card"]), job["title"], DIR / f"{job['name']}_cover.jpg", sub="3 GOALS IN ONE GAME",
                color="red", bg=str(frame))
    (DIR / f"{job['name']}.txt").write_text(job["caption"], encoding="utf-8")
    for f in [*segs, lst, joined, frame]:
        f.unlink(missing_ok=True)
    return out


def post_due():
    """Cloud: one goal Reel a day (any hour), oldest first; logged as type 'goal_reel'."""
    from fmm import poster
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    today = dt.datetime.now().strftime("%Y-%m-%d")
    done = {Path(e.get("file", "")).name for e in log if e.get("type") == "goal_reel"}
    if sum(1 for e in log if e.get("type") == "goal_reel" and e.get("at", "")[:10] == today) >= 2:
        return None  # max 2 a day (owner: trend posts like the CR7 tribute can't wait a day)
    # special_N_*.png/.mp4 = owner's special posts (concept cards, tributes), posted in N order; photos get their Reel
    items = sorted(DIR.glob("special_*"))  # owner 19 Nov: gameplay goal Reels paused, concept/special posts only
    for f in items:
        if f.suffix not in (".mp4", ".png") or f.name.endswith(("_cover.jpg", "_reel.mp4")):
            continue
        cap = f.with_suffix(".txt")
        if f.name in done or not cap.exists():
            continue
        kind = "reel" if f.suffix == ".mp4" else "photo"
        return poster.post(kind, f, cap.read_text(encoding="utf-8"), "both", "goal_reel")
    return None


if __name__ == "__main__":
    if sys.argv[1:2] == ["make"]:
        for j in JOBS:
            if not (DIR / f"{j['name']}.mp4").exists():
                print("made", make(j))
