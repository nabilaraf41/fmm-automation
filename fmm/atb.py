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


def clip(seed):
    return _pick(CLIPS, seed)


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
    assert badge("x") == badge("x") and clip("a") in CLIPS, "deterministic pick"
    im = add_badge(Image.new("RGB", (1080, 1350), (10, 10, 10)), "test")
    assert im.size == (1080, 1350) and im.getpixel((1080 - 22 - 75, 1350 - 78 - 75)) != (10, 10, 10)
    print(len(BADGES), "badges,", len(CLIPS), "clips: ok")
