"""Background music for Reels: YouTube Audio Library tracks marked "Attribution not required" (assets/music/).

Those tracks are licensed for any video on any platform, no credit needed (owner rule: never risk copyright).
Only add tracks from that filter; never trending/commercial songs.
"""
import random
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "assets" / "music"


def pick(seed=None):
    """(track path, start offset in seconds) or (None, 0) when no music is installed."""
    tracks = sorted(DIR.glob("*.mp3"))
    if not tracks:
        return None, 0
    rnd = random.Random(seed)
    return str(rnd.choice(tracks)), rnd.choice([0, 8, 15, 25])  # skip quiet intros now and then
