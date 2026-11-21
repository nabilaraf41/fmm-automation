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
}, {
    # 21 Nov: goals found by the scoreboard change (tools/goal_detect_study.py), scorer read from the game's own pop-up
    "name": "g1_nico_williams_25", "source": "output/inbox/1BQ-oyjyMStrkbnbU_7IXzCPx9i7vjoyO.mp4",
    "parts": [(106.5, 114.5, "25'")], "title": "NICO WILLIAMS 124 GOAL", "card": "assets/cards/rz/ingame_nico_williams_124.png",
    "caption": "124 Nico Williams Goal 🔥🇪🇸\n\nWould you have scored this? Rate it 1-10 👇\n\n#FCMobile #FIFAMobile #EAFC #NicoWilliams #FMM",
}, {
    "name": "g2_dembele_68", "source": "output/inbox/1BQ-oyjyMStrkbnbU_7IXzCPx9i7vjoyO.mp4",
    "parts": [(254.0, 262.0, "68'")], "title": "DEMBELE 127 GOAL", "card": "assets/cards/rz/ingame_dembele_127.png",
    "caption": "127 Dembélé Goal 🥶🇫🇷\n\nIs this card worth it? 👇\n\n#FCMobile #FIFAMobile #EAFC #Dembele #FMM",
}, {
    "name": "g3_dembele_79", "source": "output/inbox/1BQ-oyjyMStrkbnbU_7IXzCPx9i7vjoyO.mp4",
    "parts": [(300.3, 308.3, "79'")], "title": "DEMBELE AGAIN!!", "card": "assets/cards/rz/ingame_dembele_127.png",
    "caption": "127 Dembélé Scores Again 💀🔥\n\nSecond goal of the match. Best ST in the game right now? 👇\n\n#FCMobile #FIFAMobile #EAFC #Dembele #FMM",
}, {
    # 22 Nov upgrade: vote Reel ("Who deserves the best goal?" 1.5M, "Pick one, Puskas" 13.7M) from the 3 verified goals
    "name": "g4_best_goal_vote", "source": "output/inbox/1BQ-oyjyMStrkbnbU_7IXzCPx9i7vjoyO.mp4",
    "parts": [(106.5, 114.5, "GOAL 1", "assets/cards/rz/ingame_nico_williams_124.png"), (254.0, 262.0, "GOAL 2"),
              (300.3, 308.3, "GOAL 3")],
    "title": "BEST GOAL? 1, 2 OR 3", "card": "assets/cards/rz/ingame_dembele_127.png",
    "caption": "Which goal is the best? 1, 2 or 3 🤔⚽\n\n1. 124 Nico Williams\n2. 127 Dembélé\n3. 127 Dembélé again\n\nComment your pick 👇\n\n#FCMobile #FIFAMobile #EAFC #FCMobileGoals #FMM",
}]


def make(job):
    DIR.mkdir(parents=True, exist_ok=True)
    out = DIR / f"{job['name']}.mp4"
    src = ROOT / job["source"]
    segs = []
    for i, (a, b, label, *card) in enumerate(job["parts"]):  # optional 4th item = that goal's scorer card
        ov = overlay_png(job["title"], label, DIR / f"_ov{i}.png", ROOT / (card[0] if card else job["card"]), title_y=430)  # below ATB box
        seg = DIR / f"_seg{i}.mp4"
        vf = (f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS,split=2[x][y];"
              f"[x]scale=-2:{RH},crop={RW}:{RH},boxblur=25:2,eq=brightness=-0.12:saturation=1.3[bg];"
              f"[y]scale=2000:-2,crop=1080:ih:(iw-1080)/2:0,{LOOK}[fg];"
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
    total = sum(b - a for a, b, *_ in job["parts"])
    hits, t = [], 0.0
    for a, b, *_ in job["parts"]:
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
    items = sorted(DIR.glob("special_*"))
    # owner 21 Nov: gameplay goal Reels back (scoreboard-verified goals, g*_ jobs), NEVER more than 1 a day
    if not any(e.get("type") == "goal_reel" and e.get("at", "")[:10] == today and Path(e.get("file", "")).name.startswith("g")
               and not Path(e.get("file", "")).name.startswith("goal") for e in log):
        items += sorted(DIR.glob("g[0-9]*_*.mp4"))
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
