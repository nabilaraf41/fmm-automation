"""Click-worthy covers for Reels/Shorts (MrBeast / FC-Mobile-creator style).

Rules: one huge subject (the card), 2–4 huge words in yellow/white with a thick black outline,
saturated burst background, a shocked emoji and a red arrow pointing at the subject.

    cover(card_path, "MUST BUY?!", out_path, sub="124 OVR", color="red")
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from fmm.brand import font, EMOJI, LOGO, load_card

W, H = 1080, 1920
THEMES = {  # burst colours (inner, outer)
    "red": ((255, 60, 40), (120, 0, 10)), "gold": ((255, 210, 40), (150, 70, 0)),
    "blue": ((60, 170, 255), (10, 30, 120)), "purple": ((190, 90, 255), (60, 0, 110)),
    "green": ((60, 255, 140), (0, 90, 40)),
}


def burst(inner, outer, cx, cy, rays=28):
    bg = Image.new("RGB", (W, H), outer)
    d = ImageDraw.Draw(bg)
    R = 2400
    for i in range(rays):
        a0, a1 = 2 * math.pi * i / rays, 2 * math.pi * (i + 0.5) / rays
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))],
                  fill=tuple(int(o + (n - o) * 0.35) for o, n in zip(outer, inner)))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((cx - 650, cy - 650, cx + 650, cy + 650), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(260))
    bg = Image.composite(Image.new("RGB", (W, H), inner), bg, glow.point(lambda v: int(v * 0.85)))
    vig = Image.radial_gradient("L").resize((W, H)).point(lambda v: int(min(255, v * 1.3)))
    return Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, vig.point(lambda v: int(v * 0.6))).convert("RGBA")


def big_text(s, size, fill=(255, 230, 0), stroke=16, max_w=W - 80):
    f = font("Anton-Regular.ttf", size)
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    while d0.textlength(s, font=f) > max_w and size > 60:
        size -= 6; f = font("Anton-Regular.ttf", size)
    l, t, r, b = d0.textbbox((0, 0), s, font=f, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20 - l, 20 - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.paste(Image.new("RGBA", im.size, (0, 0, 0, 200)), (0, 0), im)
    out = Image.new("RGBA", (im.width + 24, im.height + 24), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), (16, 18))
    out.alpha_composite(im, (0, 0))
    return out.rotate(3, resample=Image.BICUBIC, expand=True)


def arrow(length=360, width=70, color=(255, 30, 30)):
    im = Image.new("RGBA", (length + 40, width * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = im.height // 2
    pts = [(20, cy - width // 2), (length - width * 1.4, cy - width // 2), (length - width * 1.4, cy - width * 1.3),
           (length + 20, cy), (length - width * 1.4, cy + width * 1.3), (length - width * 1.4, cy + width // 2),
           (20, cy + width // 2)]
    d.polygon(pts, fill=(0, 0, 0), outline=(0, 0, 0))
    out = im.filter(ImageFilter.MaxFilter(17))
    ImageDraw.Draw(out).polygon(pts, fill=color)
    return out


def cover(subject_path, text, out_path, sub=None, color="red", emoji="wow", flip_arrow=False, bg=None):
    """bg = optional photo (e.g. the goal frame) blended under the burst rays."""
    inner, outer = THEMES.get(color, THEMES["red"])
    img = burst(inner, outer, W // 2, 1130)
    if bg and Path(bg).exists():
        ph = Image.open(bg).convert("RGB")
        s = max(W / ph.width, H / ph.height)
        ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
        ph = ph.crop(((ph.width - W) // 2, (ph.height - H) // 2, (ph.width + W) // 2, (ph.height + H) // 2))
        ph = ImageEnhance.Color(ImageEnhance.Brightness(ph).enhance(0.75)).enhance(1.4).convert("RGBA")
        img = Image.blend(ph, img, 0.45)
    # subject: card, huge, punchy colours, white rim + glow
    card = load_card(subject_path) if subject_path else None
    if card:
        card = ImageEnhance.Color(ImageEnhance.Contrast(card.convert("RGBA")).enhance(1.15)).enhance(1.25)
        s = 1220 / card.height
        card = card.resize((int(card.width * s), int(card.height * s)), Image.LANCZOS)
        if card.width > 1000:
            card = card.resize((1000, int(card.height * 1000 / card.width)), Image.LANCZOS)
        rim = Image.new("RGBA", card.size, (0, 0, 0, 0))
        rim.paste(Image.new("RGBA", card.size, (255, 255, 255, 255)), (0, 0), card)
        rim = rim.filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(3))
        glow = Image.new("RGBA", card.size, (0, 0, 0, 0))
        glow.paste(Image.new("RGBA", card.size, (255, 255, 200, 230)), (0, 0), card)
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        x, y = (W - card.width) // 2, 1130 - card.height // 2 + 80
        img.alpha_composite(glow, (x, y)); img.alpha_composite(rim, (x, y)); img.alpha_composite(card, (x, y))
    # headline (2–4 words), top third
    lines = text.upper().split("\n") if "\n" in text else [text.upper()]
    y = 70
    for i, ln in enumerate(lines[:2]):
        t = big_text(ln, 230 if len(lines) == 1 else 190, (255, 230, 0) if i == 0 else (255, 255, 255))
        img.alpha_composite(t, ((W - t.width) // 2, y)); y += t.height - 40
    if sub:
        t = big_text(sub.upper(), 120, (255, 255, 255), stroke=12)
        img.alpha_composite(t, ((W - t.width) // 2, H - t.height - 70))
    # shocked emoji + red arrow pointing at the card
    em = Image.open(EMOJI / f"{emoji}.png").convert("RGBA")
    em = em.resize((260, int(260 * em.height / em.width)), Image.LANCZOS).rotate(-12, expand=True, resample=Image.BICUBIC)
    a = arrow().rotate(-35 if not flip_arrow else 215, expand=True, resample=Image.BICUBIC)
    # emoji low on the side (never over the OVR, which sits top-left on cards); arrow top-right
    if not flip_arrow:
        img.alpha_composite(em, (10, 1330)); img.alpha_composite(a, (W - a.width - 10, 600))
    else:
        img.alpha_composite(em, (W - em.width - 10, 1330)); img.alpha_composite(a, (10, 600))
    # small brand mark
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255))
    logo.thumbnail((200, 100))
    img.alpha_composite(logo, (30, 30))
    out_path = Path(out_path)
    img.convert("RGB").save(out_path, quality=92)
    return out_path


if __name__ == "__main__":
    import sys
    print(cover(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "output/_cover.jpg",
                sub=sys.argv[4] if len(sys.argv) > 4 else None))
