"""Turn a branded post (or any image) into a 9:16 Reel/Short with slow zoom + music.

Usage:  python -m fmm.reel output/day1_tip.png [music.mp3] [seconds]
Output: output/<name>_reel.mp4 (1080x1920, H.264, 30fps) â€” fits FB Reels, IG Reels, YT Shorts.
"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageFilter

FPS = 30


def make_frame(src: Path) -> Path:
    """Place the 4:5 post on a blurred 9:16 canvas."""
    post = Image.open(src).convert("RGB")
    canvas = post.resize((1080, 1920)).filter(ImageFilter.GaussianBlur(40))
    canvas = Image.blend(canvas, Image.new("RGB", canvas.size, (5, 5, 5)), 0.55)
    post = post.resize((1080, 1350))
    canvas.paste(post, (0, (1920 - 1350) // 2))
    out = src.with_name(src.stem + "_916.png")
    canvas.save(out)
    return out


def make_reel(src, music=None, seconds=8):
    src = Path(src)
    frame = make_frame(src)
    out = src.with_name(src.stem + "_reel.mp4")
    n = seconds * FPS
    # 4K source + gentle zoom keeps small stat text crisp; unsharp offsets the platforms' recompression
    vf = (f"scale=4320:-1:flags=lanczos,zoompan=z='min(zoom+0.0003,1.05)':x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps={FPS},unsharp=5:5:0.8,fade=t=in:st=0:d=0.5,format=yuv420p")
    start = 0
    if not music:  # copyright-safe library track (fmm.music), else a silent track: platforms prefer an audio stream
        from fmm import music as lib
        music, start = lib.pick()
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(frame)]
    if music:
        cmd += ["-ss", str(start), "-i", str(music), "-af", f"afade=t=in:d=0.5,afade=t=out:st={seconds - 1}:d=1,loudnorm=I=-16:TP=-1.5"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-vf", vf, "-t", str(seconds), "-c:v", "libx264", "-preset", "slow", "-crf", "16",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    frame.unlink()
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    print("made", make_reel(a[0], a[1] if len(a) > 1 else None, int(a[2]) if len(a) > 2 else 8))
