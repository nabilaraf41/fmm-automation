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
EA = sorted((ROOT / "assets" / "atb_ea").glob("*.mp4"))  # EA-logic comedy + hooks WITH his voice ("EA... why?")


# owner (12 Nov): followers asked for sound -> every Reel gets ATB's VOICE with a line that fits the post
# (lines transcribed into content/atb_voice.json). Post type -> clips whose line suits it.
_A = ROOT / "assets"
VOICE = {k: [_A / x for x in v] for k, v in {
    "statrank": ["atb_pack/n_j07.mp4", "atb_pack/p_038.mp4", "atb_pack/n_p03.mp4", "atb_pack/p_001.mp4", "atb_pack/n_p06.mp4"],
    "rank10": ["atb_pack/n_j07.mp4", "atb_pack/p_038.mp4", "atb_pack/n_p03.mp4", "atb_pack/p_001.mp4"],
    "xi": ["atb_pack/n_j03.mp4", "atb_pack/n_j06.mp4", "atb_pack/n_p03.mp4", "atb_pack/n_p02.mp4"],
    "choose": ["atb_pack/n_p03.mp4", "atb_clips/46_stunned_blink.mp4", "atb_pack/n_p06.mp4", "atb_pack/p_001.mp4"],
    "newcard": ["atb_pack/p_071.mp4", "atb_pack/p_076.mp4", "atb_pack/n_j03.mp4", "atb_pack/n_j06.mp4"],
    "review": ["atb_pack/p_076.mp4", "atb_pack/n_j03.mp4", "atb_pack/n_j06.mp4", "atb_pack/n_j07.mp4"],
    "code": ["atb_pack/n_p02.mp4", "atb_pack/n_p10.mp4", "atb_pack/p_045.mp4", "atb_clips/02_celebration.mp4"],
    "leak": ["atb_pack/n_p06.mp4", "atb_pack/n_p03.mp4", "atb_pack/p_046.mp4"],
    "stopgame": ["atb_pack/n_p06.mp4", "atb_pack/n_p03.mp4"],
    "default": ["atb_pack/n_p03.mp4", "atb_pack/n_j07.mp4", "atb_pack/p_038.mp4", "atb_clips/01_shocked.mp4",
                "atb_clips/49_nodding_hype.mp4"],
}.items()}


def voiced(kind):
    """A voiced ATB clip whose line fits this post type (least recently used); default lines otherwise."""
    items = [c for c in VOICE.get(kind or "", VOICE["default"]) if c.exists()] or [c for c in VOICE["default"] if c.exists()]
    return clip(kind, items=items) if items else None


def clip(seed=None, pool=None, items=None):
    """Least-recently-used reaction clip (owner: never the same clip again and again). Usage is saved in
    content/clips_state.json -> "atb_used" (merged by fmm.savestate), so it rotates across cloud runs."""
    import datetime as dt, json
    items = items or {"pack": PACK, "ea": EA}.get(pool) or CLIPS
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


def _has_audio(p):
    import subprocess
    return bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


def box(mp4, seed, y=140, pool=None, voice=None):
    """Reaction video: ATB's clip boxed top-right over a Reel for its whole length (in place). Owner rule:
    no Reel without his video. Keeps the Reel's own audio; pool="ea" also mixes in his voice line (first 6 s)."""
    import subprocess
    c = voiced(voice) if voice else clip(seed, pool=pool)
    if not c:  # no Reel without ATB: raising stops the build, so nothing posts
        raise RuntimeError(f"no ATB clip ({pool or 'atb_clips'}): Reel not made")
    mp4 = Path(mp4)
    tmp = mp4.with_name(mp4.stem + "_atb.mp4")
    fc = f"[1:v]scale=440:248,pad=452:260:6:6:color=0xE11D2E[p];[0:v][p]overlay=W-w-28:{y}:shortest=1[v]"
    amap, acodec = ["-map", "0:a?"], ["-c:a", "copy"]
    if (pool == "ea" or voice) and _has_audio(c):
        voice = "[1:a]atrim=0:6,asetpts=PTS-STARTPTS,volume=1.4,apad"
        if _has_audio(mp4):
            fc += f";{voice}[vo];[0:a]volume=0.6[g];[g][vo]amix=inputs=2:duration=first:normalize=0[a]"
        else:
            fc += f";{voice}[a]"
        amap, acodec = ["-map", "[a]", "-shortest"], ["-c:a", "aac", "-b:a", "160k"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-stream_loop", "-1", "-i", str(c), "-filter_complex",
                    fc, "-map", "[v]", *amap, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", *acodec, "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(mp4)
    return mp4


def add_badge(img, seed, size=150, margin=22, bottom=78):
    """Small round ATB face in the bottom-right corner of a photo post, above the footer line."""
    b = badge(seed)
    if not b:  # every post shows ATB: no badge -> no photo
        raise RuntimeError("no ATB badge in assets/atb_face: photo not made")
    face = Image.open(b).convert("RGBA").resize((size, size), Image.LANCZOS)
    out = img.convert("RGBA")
    out.alpha_composite(face, (out.width - size - margin, out.height - size - bottom))
    return out.convert("RGB")


if __name__ == "__main__":
    assert badge("x") == badge("x"), "deterministic badge"
    im = add_badge(Image.new("RGB", (1080, 1350), (10, 10, 10)), "test")
    assert im.size == (1080, 1350) and im.getpixel((1080 - 22 - 75, 1350 - 78 - 75)) != (10, 10, 10)
    print(len(BADGES), "badges,", len(CLIPS), "clips: ok")
