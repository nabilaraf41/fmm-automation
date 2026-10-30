"""Turn a branded post (or any image) into a 9:16 Reel/Short with slow zoom + music.

Usage:  python -m fmm.reel output/day1_tip.png [music.mp3] [seconds]
Output: output/<name>_reel.mp4 (1080x1920, H.264, 30fps) — fits FB Reels, IG Reels, YT Shorts.
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
    vf = (f"scale=2160:-1,zoompan=z='min(zoom+0.0008,1.12)':x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps={FPS},fade=t=in:st=0:d=0.5,format=yuv420p")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(frame)]
    if music:
        cmd += ["-i", str(music)]
    else:  # silent track — platforms prefer an audio stream
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-vf", vf, "-t", str(seconds), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    frame.unlink()
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    print("made", make_reel(a[0], a[1] if len(a) > 1 else None, int(a[2]) if len(a) > 2 else 8))
