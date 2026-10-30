"""Remove card/player backgrounds and upscale + sharpen to HD.

Needs the Python 3.12 env (rembg has no build for 3.15):
    .venv312\Scripts\python -m fmm.clean assets/cards            -> assets/cards_hd/*.png
    .venv312\Scripts\python -m fmm.clean path/to/photo.jpg       -> same folder, *_hd.png
    .venv312\Scripts\python -m fmm.clean --person assets/heroes  -> player photo cut-outs
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from rembg import remove, new_session

TARGET_H = 1400  # output height in px — enough for full-size use on a 1080x1350 post
SESSION = None


def clean(src: Path, out: Path, model="isnet-general-use", person=False):
    global SESSION
    SESSION = SESSION or new_session(model)
    im = Image.open(src).convert("RGBA")
    # upscale first so the cut-out edge is computed at higher resolution
    s = max(1.0, TARGET_H / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    cut = im.copy()
    if person:
        # player photo: keep exactly what the AI mask finds (no hole filling)
        alpha = remove(im, session=SESSION, only_mask=True, post_process_mask=True)
    elif min(im.getpixel((2, 2))[:3]) > 225:
        # plain white background (card renders): remove only the white connected to the edges
        for xy in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
            ImageDraw.floodfill(cut, xy, (0, 0, 0, 0), thresh=40)
        alpha = cut.getchannel("A")
    else:
        # photo/screenshot: AI mask, then fill holes so the whole card stays (AI tends to keep only the player)
        mask = remove(im, session=SESSION, only_mask=True, post_process_mask=True).point(lambda v: 255 if v > 100 else 0)
        outside = mask.convert("RGB")
        ImageDraw.floodfill(outside, (0, 0), (255, 0, 0), thresh=10)
        alpha = Image.eval(outside.getchannel("G"), lambda v: 255 if v > 0 else 0)  # everything not reached = card
        alpha = alpha.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1))
    cut.putalpha(alpha)
    cut = cut.crop(alpha.point(lambda v: 255 if v > 20 else 0).getbbox())
    rgb, alpha = cut.convert("RGB"), cut.getchannel("A")
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb.putalpha(alpha)
    out.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(out, optimize=True)
    return out


if __name__ == "__main__":
    person = "--person" in sys.argv  # use for player photos (spotlight heroes), not cards
    target = Path([a for a in sys.argv[1:] if a != "--person"][0])
    files = sorted(p for p in target.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")) \
        if target.is_dir() else [target]
    for f in files:
        dest = (target.parent / (target.name + "_hd") / f"{f.stem}.png") if target.is_dir() \
            else f.with_name(f.stem + "_hd.png")
        print("cleaned", clean(f, dest, person=person))
