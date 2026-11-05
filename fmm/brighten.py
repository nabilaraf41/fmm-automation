"""Owner rule: ATB must look bright and fair, never dark. Lifts skin tones (soft skin mask) more than the rest.

    python -m fmm.brighten <file-or-folder> [...]   -> edits images in place (keeps a copy in ./original/)
"""
import sys, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter


def brighten(im):
    rgb = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cr, cb = (r - y) * 0.713 + 0.5, (b - y) * 0.564 + 0.5
    # skin, not red LED walls: real skin keeps green at >= ~55% of red and blue below green
    skin = ((cr > 0.52) & (cr < 0.68) & (cb > 0.36) & (cb < 0.52) & (y > 0.12)
            & (g > 0.55 * r) & (b < g * 1.05)).astype(np.float32)
    m = np.asarray(Image.fromarray((skin * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(6))) / 255.0
    m = m[..., None]
    lifted = rgb ** (1 / 1.25)                                    # ~20% lighter skin (owner: not more)
    lifted = lifted * 0.93 + lifted.mean(-1, keepdims=True) * 0.07  # a little less saturated = fairer look
    base = np.clip(rgb ** (1 / 1.05), 0, 1)                       # gentle lift everywhere else
    out = np.clip(base * (1 - m) + lifted * m, 0, 1)
    res = Image.fromarray((out * 255).astype("uint8"))
    if im.mode == "RGBA":
        res.putalpha(im.getchannel("A"))
    return res


def run(paths):
    for p in paths:
        p = Path(p)
        for f in ([p] if p.is_file() else sorted(p.glob("*.png")) + sorted(p.glob("*.jpg"))):
            keep = f.parent / "original" / f.name
            if keep.exists():
                continue  # already done
            keep.parent.mkdir(exist_ok=True)
            shutil.copy2(f, keep)
            brighten(Image.open(f)).save(f, quality=95)
            print("brightened", f.name)


if __name__ == "__main__":
    a = Image.new("RGB", (40, 40), (120, 80, 60))  # a skin-like tone gets lifted
    assert np.asarray(brighten(a)).mean() > np.asarray(a).mean() + 15
    run(sys.argv[1:])

