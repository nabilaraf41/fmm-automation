"""ATB (owner, host of FMM) assets: round face badges for photo posts, reaction clips for the top of Reels.

assets/atb_face/badge_*.png  - round face badges (from the owner's Google Flow ATB character clips)
assets/atb_clips/*.mp4       - 1080x608 silent reaction clips, shown in the top part of photo Reels
Owner rule: every post shows ATB; never a clip/frame where he looks bald or the phone screen faces the camera.
"""
import hashlib
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BADGES = sorted((ROOT / "assets" / "atb_face").glob("badge_*.png"))
CLIPS = sorted((ROOT / "assets" / "atb_clips").glob("*.mp4"))


def _pick(items, seed):
    if not items:
        return None
    return items[int(hashlib.md5(str(seed).encode()).hexdigest(), 16) % len(items)]


def badge(seed):
    return _pick(BADGES, seed)


PACK = sorted((ROOT / "assets" / "atb_pack").glob("*.mp4"))  # pack reactions WITH his voice (lines fit any pull)


def clip(seed=None, pool=None):
    """Least-recently-used reaction clip (owner: never the same clip again and again). Usage is saved in
    content/clips_state.json -> "atb_used" (merged by fmm.savestate), so it rotates across cloud runs."""
    import datetime as dt, json
    items = PACK if pool == "pack" and PACK else CLIPS
    if not items:
        return None
    sf = ROOT / "content" / "clips_state.json"
    st = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
    used = st.setdefault("atb_used", {})
    # never-used first, shuffled (so rooms/places mix instead of one batch in a row), then the one used longest ago;
    # a clip comes back only after every other clip in its pool was used
    c = min(items, key=lambda p: (used.get(p.name, ""), hashlib.md5(p.name.encode()).hexdigest()))
    used[c.name] = dt.datetime.now().isoformat(timespec="seconds")
    sf.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    return c


def box(mp4, seed, y=140):
    """Reaction video: ATB's clip boxed top-right over a Reel for its whole length (in place). Owner rule:
    no Reel without his video. Keeps the Reel's own audio."""
    import subprocess
    c = clip(seed)
    if not c:
        return mp4
    mp4 = Path(mp4)
    tmp = mp4.with_name(mp4.stem + "_atb.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-stream_loop", "-1", "-i", str(c), "-filter_complex",
                    f"[1:v]scale=440:248,pad=452:260:6:6:color=0xE11D2E[p];[0:v][p]overlay=W-w-28:{y}:shortest=1[v]",
                    "-map", "[v]", "-map", "0:a?", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(mp4)
    return mp4


def add_badge(img, seed, size=150, margin=22, bottom=78):
    """Small round ATB face in the bottom-right corner of a photo post, above the footer line."""
    b = badge(seed)
    if not b:
        return img
    face = Image.open(b).convert("RGBA").resize((size, size), Image.LANCZOS)
    out = img.convert("RGBA")
    out.alpha_composite(face, (out.width - size - margin, out.height - size - bottom))
    return out.convert("RGB")


if __name__ == "__main__":
    assert badge("x") == badge("x"), "deterministic badge"
    im = add_badge(Image.new("RGB", (1080, 1350), (10, 10, 10)), "test")
    assert im.size == (1080, 1350) and im.getpixel((1080 - 22 - 75, 1350 - 78 - 75)) != (10, 10, 10)
    print(len(BADGES), "badges,", len(CLIPS), "clips: ok")
