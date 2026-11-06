"""ATB facecam for long (16:9) H2H / VSA videos: a small box bottom-left for the whole match.

Calm loops (assets/atb_long/calm_*.mp4: head down at the phone, small glances) cycle all match long;
at each goal the box plays a goal clip (assets/atb_long/goal_*.mp4 when owner scores,
concede_*.mp4 when he concedes), with his voice. Goal times come from content/long_goals.json
(drive id -> [[seconds, "scored"|"conceded"], ...]), studied by hand like pack_trims.json.

    python -m fmm.facecam <in.mp4> <out.mp4> [t:scored ...]   -> test locally
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LONG = ROOT / "assets" / "atb_long"
W, H = 480, 270  # box size on a 1920x1080 video (bottom-left, like big creators' facecams)


def _dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip() or 0)


def timeline(total, goals):
    """[(clip, start_in_video, length)] covering 0..total: calm loops cycled, goal clips at goal times."""
    calm = sorted(LONG.glob("calm_*.mp4"))
    pools = {"scored": sorted(LONG.glob("goal_*.mp4")), "conceded": sorted(LONG.glob("concede_*.mp4"))}
    if not calm:
        return []
    out, t, ci, gi = [], 0.0, 0, {"scored": 0, "conceded": 0}
    for g_t, kind in sorted(goals) + [(total, None)]:
        while t < g_t - 0.05:  # calm loops until the goal
            c = calm[ci % len(calm)]; ci += 1
            ln = min(_dur(c), g_t - t)
            out.append((c, t, ln)); t += ln
        if kind and pools.get(kind):
            c = pools[kind][gi[kind] % len(pools[kind])]; gi[kind] += 1
            ln = min(_dur(c), total - t)
            out.append((c, t, ln)); t += ln
    return out


def add(video, out, goals=()):
    """Burn the ATB facecam into a landscape long video (keeps the game audio, adds his goal voice)."""
    video, out = Path(video), Path(out)
    total = _dur(video)
    tl = timeline(total, list(goals))
    if not tl:
        return video
    track = out.with_name(out.stem + "_cam.mp4")
    lst = out.with_name(out.stem + "_cam.txt")
    lst.write_text("".join(f"file '{c.as_posix()}'\ninpoint 0\noutpoint {ln:.3f}\n" for c, _, ln in tl), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-vf", f"scale={W}:{H},fps=30", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2", str(track)], check=True)
    has_a = lambda p: subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                      "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip()
    fc = (f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2[g];"
          f"[1:v]pad={W + 8}:{H + 8}:4:4:color=0xE11D2E[c];[g][c]overlay=24:H-h-24:shortest=1[v]")
    game, cam = has_a(video), has_a(track)
    amap = ["-map", "0:a?"]
    if game and cam:  # calm loops are silent; goal clips carry his voice
        fc += ";[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]"
        amap = ["-map", "[a]"]
    elif cam:  # screen recording without sound (owner's H2H files): his voice only
        amap = ["-map", "1:a"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(track), "-filter_complex", fc,
                    "-map", "[v]", *amap, "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac",
                    "-b:a", "160k", "-movflags", "+faststart", str(out)], check=True)
    track.unlink(missing_ok=True); lst.unlink(missing_ok=True)
    return out


def goals_for(drive_id):
    f = ROOT / "content" / "long_goals.json"
    return [tuple(g) for g in json.loads(f.read_text(encoding="utf-8")).get(drive_id, [])] if f.exists() else []


if __name__ == "__main__":
    a = sys.argv[1:]
    gs = [(float(x.split(":")[0]), x.split(":")[1]) for x in a[2:]]
    print(add(a[0], a[1], gs))
