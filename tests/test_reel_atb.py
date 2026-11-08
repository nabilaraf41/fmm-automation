"""python tests/test_reel_atb.py: nothing is made without ATB (photo Reel, review/clip/EA Reels, photo badge)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image
from fmm import atb, reel

atb.clip = lambda *a, **k: None
atb.badge = lambda *a, **k: None
for name, fn in [("photo Reel", lambda: reel.make_reel("nothing.png")),
                 ("review/clip/EA Reel (atb.box)", lambda: atb.box("nothing.mp4", "x")),
                 ("photo badge", lambda: atb.add_badge(Image.new("RGB", (10, 10)), "x"))]:
    try:
        fn()
    except RuntimeError as e:
        assert "ATB" in str(e), e
        print("ok:", name, "-> stops without ATB")
    else:
        raise AssertionError(name + " was made without ATB")
