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
    em = Image.open(EMOJI / f"{emoji or 'wow'}.png").convert("RGBA")
    from fmm import atb
    face = atb.badge(f"{text}{emoji}")  # owner rule: ATB's real reaction instead of a cartoon emoji
    if face and emoji is not None:
        em = Image.open(face).convert("RGBA")
    if emoji is None:
        em = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
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


FACES = sorted((Path(__file__).resolve().parent.parent / "assets" / "atb").glob("thumb_*.png"))


def face_for(n):
    """ATB reaction cutout for long-video thumbnail n (rotates so the channel page doesn't repeat one face)."""
    return FACES[n % len(FACES)] if FACES else None


def cover_wide(frame, text, out_path, card=None, sub=None, big=None, emoji="wow", face=None):
    if face:  # owner rule (10 Nov): ATB face ~50% of the thumbnail, like Vishy/RkReddy/De MYSTeRIO covers
        return _cover_face(frame, text, out_path, card, face)
    """big = huge right-side text (e.g. the score "4-0") when there is no card."""
    """16:9 thumbnail (1280x720) for long videos: punchy frame, huge outlined text left, card right, red arrow."""
    w, h = 1280, 720
    img = Image.new("RGBA", (w, h), (10, 10, 10, 255))
    if frame and Path(frame).exists():
        ph = Image.open(frame).convert("RGB")
        s = max(w / ph.width, h / ph.height)
        ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
        ph = ph.crop(((ph.width - w) // 2, (ph.height - h) // 2, (ph.width + w) // 2, (ph.height + h) // 2))
        img = ImageEnhance.Color(ImageEnhance.Contrast(ph).enhance(1.2)).enhance(1.5).convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (w, h), (0, 0, 0, 70)))
    if card:
        from fmm.brand import load_card
        c = load_card(card); c.thumbnail((430, 600), Image.LANCZOS)
        g = Image.new("RGBA", c.size, (0, 0, 0, 0)); g.paste(Image.new("RGBA", c.size, (255, 230, 120, 230)), (0, 0), c)
        x, y = w - c.width - 40, (h - c.height) // 2
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(25)), (x, y)); img.alpha_composite(c, (x, y))
    y = 60
    for i, ln in enumerate(text.upper().split(chr(10))[:2]):
        t = big_text(ln, 150, (255, 230, 0) if i == 0 else (255, 255, 255), stroke=12, max_w=700 if (card or big) else 1180)
        img.alpha_composite(t, (30, y)); y += t.height - 30
    if sub:
        t = big_text(sub.upper(), 80, (255, 255, 255), stroke=10, max_w=700 if (card or big) else 1180)
        img.alpha_composite(t, (30, h - t.height - 30))
    if big and not card:
        t = big_text(big, 330, (60, 255, 120), stroke=16, max_w=520)
        img.alpha_composite(t, (w - t.width - 30, (h - t.height) // 2 - 20))
        em = Image.open(EMOJI / f"{emoji}.png").convert("RGBA")
        em = em.resize((190, int(190 * em.height / em.width)), Image.LANCZOS)
        img.alpha_composite(em, (w - em.width - 40, h - em.height - 30))
    a = arrow(300, 60).rotate(-25, expand=True, resample=Image.BICUBIC)
    if card:
        img.alpha_composite(a, (w - 430 - 40 - a.width + 60, 260))
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255)); logo.thumbnail((160, 80))
    img.alpha_composite(logo, (w - logo.width - 20, 20))
    img.convert("RGB").save(out_path, quality=92)
    return Path(out_path)


def _cover_face(frame, text, out_path, card, face):
    """1280x720: gameplay bg, ATB cutout left half (head big, cut at the chest), card right, huge text top right."""
    w, h = 1280, 720
    img = Image.new("RGBA", (w, h), (10, 10, 10, 255))
    if frame and Path(frame).exists():
        ph = Image.open(frame).convert("RGB")
        s = max(w / ph.width, h / ph.height)
        ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
        ph = ph.crop(((ph.width - w) // 2, (ph.height - h) // 2, (ph.width + w) // 2, (ph.height + h) // 2))
        ph = ImageEnhance.Color(ImageEnhance.Contrast(ph).enhance(1.2)).enhance(1.5).filter(ImageFilter.GaussianBlur(3))
        img = ph.convert("RGBA")
        img.alpha_composite(Image.new("RGBA", (w, h), (0, 0, 0, 90)))
    p = Image.open(face).convert("RGBA")
    p = p.crop(p.getbbox())
    p = p.crop((0, 0, p.width, int(p.height * 0.62)))  # head + shoulders only, so the face itself is big
    s = 760 / p.height
    p = p.resize((int(p.width * s), 760), Image.LANCZOS)
    if p.width > 700:  # keep the face centred in the left half
        cx = p.width // 2
        p = p.crop((cx - 350, 0, cx + 350, p.height))
    rim = Image.new("RGBA", p.size, (255, 255, 255, 255)); glow = Image.new("RGBA", p.size, (0, 0, 0, 0))
    glow.paste(rim, (0, 0), p.split()[3])
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)), (-20, h - p.height + 40))
    img.alpha_composite(p, (-20, h - p.height + 40))
    if card:
        c = load_card(card); c.thumbnail((400, 560), Image.LANCZOS)
        g = Image.new("RGBA", c.size, (0, 0, 0, 0)); g.paste(Image.new("RGBA", c.size, (255, 230, 120, 230)), (0, 0), c)
        x, y = w - c.width - 50, h - c.height - 30
        img.alpha_composite(g.filter(ImageFilter.GaussianBlur(25)), (x, y)); img.alpha_composite(c, (x, y))
        a = arrow(220, 55).rotate(-160, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(a, (x - a.width + 30, y + 120))
    t = big_text(text, 140, (255, 230, 0), stroke=12, max_w=620)
    img.alpha_composite(t, (w - t.width - 30 if not card else 640, 20))
    img.convert("RGB").save(out_path, quality=92)
    return Path(out_path)
