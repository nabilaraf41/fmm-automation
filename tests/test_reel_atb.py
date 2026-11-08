"""python tests/test_reel_atb.py: make_reel must refuse to build a Reel without an ATB clip."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fmm import atb, reel

atb.clip = lambda *a, **k: None
try:
    reel.make_reel("nothing.png")
except RuntimeError as e:
    assert "ATB" in str(e)
    print("ok: no ATB clip -> RuntimeError")
else:
    raise AssertionError("make_reel built a Reel without ATB")
