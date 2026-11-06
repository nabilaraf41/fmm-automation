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
OW, OH = 2560, 1440  # 1440p: YouTube gives 1440p+ uploads its sharper VP9 encode (source is 1080p, 4K adds little)
from fmm.clips import LOOK  # shared gameplay sharpen + grade
W, H = 640, 360  # facecam box, bottom-left like big creators' facecams (= assets/atb_long size, no upscale)


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
    """Burn the ATB facecam into a landscape long video (output 2560x1440) (keeps the game audio, adds his goal voice)."""
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
    fc = (f"[0:v]scale={OW}:{OH}:force_original_aspect_ratio=decrease:flags=lanczos,pad={OW}:{OH}:(ow-iw)/2:(oh-ih)/2,fps=60,{LOOK}[g];"
          f"[1:v]pad={W + 8}:{H + 8}:4:4:color=0xE11D2E[c];[g][c]overlay=32:H-h-32:shortest=1[v]")
    game, cam = has_a(video), has_a(track)
    amap = ["-map", "0:a?"]
    if game and cam:  # calm loops are silent; goal clips carry his voice
        fc += ";[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]"
        amap = ["-map", "[a]"]
    elif cam:  # screen recording without sound (owner's H2H files): his voice only
        amap = ["-map", "1:a"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(track), "-filter_complex", fc,
                    "-map", "[v]", *amap, "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-c:a", "aac",  # veryfast: the cloud runner encodes 1440p in time
                    "-b:a", "160k", "-movflags", "+faststart", str(out)], check=True)
    track.unlink(missing_ok=True); lst.unlink(missing_ok=True)
    return out


def highlight(video, goals, out, n=3):
    """Vertical Instagram Reel from a long video: up to n goals (scored first), 11 s each, game at the bottom,
    ATB's goal/concede reaction big on top (pack-Reel layout), his voice. Writes out + out_cover.jpg."""
    video, out = Path(video), Path(out)
    picks = sorted(sorted(goals, key=lambda g: g[1] != "scored")[:n])
    if not picks:
        return None
    pools = {"scored": sorted(LONG.glob("goal_*.mp4")), "conceded": sorted(LONG.glob("concede_*.mp4"))}
    total, game_a, segs = _dur(video), _has_a(video), []
    for i, (t, kind) in enumerate(picks):
        cam = pools[kind][i % len(pools[kind])]
        s = max(0.0, t - 6)
        seg = out.with_name(f"{out.stem}_seg{i}.mp4")
        # ATB clip starts calm and reacts ~2 s in: start it 4.5 s into the segment so he reacts as the ball goes in
        fc = ("[0:v]split=2[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=25:2,eq=brightness=-0.15:saturation=1.3[bg];"
              f"[b]scale=1080:-2:flags=lanczos,{LOOK}[fg];[bg][fg]overlay=(W-w)/2:1000[base];"
              "[1:v]scale=1350:760,crop=1080:760,fps=30,tpad=start_duration=4.5:start_mode=clone:stop_duration=4:stop_mode=clone[t];"
              "[base][t]overlay=0:0,fps=30,format=yuv420p[v];"
              "[1:a]aresample=44100,adelay=4500|4500,volume=1.3,apad[vo]")
        fc += ";[0:a]aresample=44100,volume=0.7[g];[g][vo]amix=inputs=2:duration=longest:normalize=0[a]" if game_a else ";[vo]anull[a]"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.2f}", "-t", "11", "-i", str(video), "-i", str(cam),
                        "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", "11", "-c:v", "libx264", "-crf", "20",
                        "-preset", "medium", "-c:a", "aac", "-ar", "44100", "-ac", "2", str(seg)], check=True)
        segs.append(seg)
    lst = out.with_name(out.stem + "_segs.txt")
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in segs), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    "-movflags", "+faststart", str(out)], check=True)
    # cover: ATB mid-celebration over the first goal (never a black/faded frame)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "8", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                    str(out.with_name(out.stem + "_cover.jpg"))], check=True)
    for p in segs + [lst]:
        p.unlink(missing_ok=True)
    return out


def _has_a(p):
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


def goals_for(drive_id):
    f = ROOT / "content" / "long_goals.json"
    return [tuple(g) for g in json.loads(f.read_text(encoding="utf-8")).get(drive_id, [])] if f.exists() else []


if __name__ == "__main__":
    a = sys.argv[1:]
    gs = [(float(x.split(":")[0]), x.split(":")[1]) for x in a[2:]]
    print(add(a[0], a[1], gs))
