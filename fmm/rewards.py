"""Reward visuals for redeem-code posts.

pick(reward_text) -> path of the best image for that reward.
Your own game screenshots win: drop them in assets/rewards/ as gems.png, mls.png, draft.png, player.png,
coins.png, pack.png (transparent PNG best). Missing ones are drawn here in FMM style (python -m fmm.rewards).
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "assets" / "rewards"
GEN = DIR / "generated"

# keyword -> reward type (first match wins, so specific words come first)
KEYWORDS = [("draft", "draft"), ("rank", "rankup"), ("gem", "gems"), ("mls", "mls"), ("coin", "coins"),
            ("fcp", "tokens"), ("fc point", "tokens"), ("token", "tokens"), ("shard", "tokens"), ("pack", "pack"), ("mystery", "pack"),
            ("ballon", "player"), ("icon", "player"), ("player", "player"), ("ovr", "player")]
REAL = DIR / "src_hd"  # real game images you supplied (backgrounds removed by fmm.clean)
S = 800  # canvas size


def _glow(im, color, blur=40, strength=200):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    g.paste(Image.new("RGBA", im.size, color + (strength,)), (0, 0), im)
    g = g.filter(ImageFilter.GaussianBlur(blur))
    g.alpha_composite(im)
    return g


def draw_gems():
    """Cut gem, in FC Mobile's blue-gem colours, 3 stacked."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    def gem(cx, cy, w):
        h = w * 0.85
        top, mid, bot = cy - h * .45, cy - h * .1, cy + h * .55
        d = ImageDraw.Draw(im)
        crown = [(cx - w * .5, mid), (cx - w * .3, top), (cx + w * .3, top), (cx + w * .5, mid)]
        d.polygon(crown + [(cx, bot)][:0], fill=(120, 200, 255))
        d.polygon([(cx - w * .5, mid), (cx + w * .5, mid), (cx, bot)], fill=(30, 120, 230))
        d.polygon([(cx - w * .3, top), (cx, mid), (cx - w * .5, mid)], fill=(170, 225, 255))
        d.polygon([(cx + w * .3, top), (cx, mid), (cx + w * .5, mid)], fill=(90, 175, 250))
        d.polygon([(cx - w * .3, top), (cx + w * .3, top), (cx, mid)], fill=(210, 240, 255))
        d.polygon([(cx - w * .5, mid), (cx, bot), (cx - w * .12, mid)], fill=(60, 150, 245))
        d.polygon([(cx + w * .5, mid), (cx, bot), (cx + w * .12, mid)], fill=(20, 95, 200))
        d.line([(cx - w * .18, top + h * .08), (cx - w * .05, top + h * .08)], fill=(255, 255, 255), width=int(w * .03))
    gem(S * .32, S * .58, 300); gem(S * .68, S * .58, 300); gem(S * .5, S * .40, 380)
    return _glow(im, (40, 150, 255))


def _card(fill_top, fill_bot, rim, label, sub):
    from fmm.brand import silhouette, font, label_font
    cw, ch = 520, 720
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    grad = Image.new("RGB", (1, ch))
    for y in range(ch):
        t = y / ch
        grad.putpixel((0, y), tuple(int(fill_top[k] * (1 - t) + fill_bot[k] * t) for k in range(3)))
    grad = grad.resize((cw, ch))
    m = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 46, fill=255)
    card.paste(grad, (0, 0), m)
    sil = silhouette(); sil = sil.resize((int(sil.width * 440 / sil.height), 440))
    card.alpha_composite(sil, ((cw - sil.width) // 2, 130))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), 46, outline=rim, width=16)
    f = font("Anton-Regular.ttf", 110)
    while d.textlength(label, font=f) > cw - 100:
        f = font("Anton-Regular.ttf", f.size - 6)
    d.text((50, 30), label, font=f, fill=(255, 255, 255))
    d.rectangle((16, ch - 150, cw - 16, ch - 60), fill=(5, 5, 5, 200))
    d.text((cw // 2, ch - 105), sub, font=label_font(54), fill=rim, anchor="mm")
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    im.alpha_composite(card, ((S - cw) // 2, (S - ch) // 2))
    return _glow(im, rim[:3])


def draw_mls(ovr="116+"):
    return _card((30, 40, 90), (5, 10, 30), (0, 200, 255), ovr, "MLS")


def draw_player(ovr="119+"):
    return _card((120, 90, 10), (20, 14, 0), (255, 215, 0), ovr, "PLAYER")


def ovr_label(reward):
    """'116–118 OVR MLS Player' -> '116-118'; '120 OVR' -> '120'; nothing -> None."""
    import re
    m = re.search(r"(\d{2,3})\s*[-–—]\s*(\d{2,3})", reward) or re.search(r"(\d{2,3})\s*\+?\s*OVR", reward, re.I)
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}" if m.lastindex == 2 else m.group(1)


def draw_draft():
    """Gold draft token coin with 'DRAFT' and a star."""
    from fmm.brand import font
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c, r = S / 2, 300
    d.ellipse((c - r, c - r + 18, c + r, c + r + 18), fill=(120, 80, 0))
    d.ellipse((c - r, c - r, c + r, c + r), fill=(255, 200, 40))
    d.ellipse((c - r * .82, c - r * .82, c + r * .82, c + r * .82), fill=(230, 160, 10))
    d.ellipse((c - r * .76, c - r * .76, c + r * .76, c + r * .76), outline=(255, 230, 120), width=8)
    pts = [(c + math.cos(math.radians(-90 + i * 36)) * (110 if i % 2 == 0 else 45),
            c - 60 + math.sin(math.radians(-90 + i * 36)) * (110 if i % 2 == 0 else 45)) for i in range(10)]
    d.polygon(pts, fill=(255, 245, 200))
    d.text((c, c + 110), "DRAFT", font=font("Anton-Regular.ttf", 120), fill=(90, 50, 0), anchor="mm")
    return _glow(im, (255, 190, 0))


def draw_coins():
    from fmm.brand import font
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, (x, y) in enumerate([(300, 520), (500, 520), (400, 430), (400, 330)]):
        d.ellipse((x - 150, y - 60 + 20, x + 150, y + 60 + 20), fill=(150, 100, 0))
        d.ellipse((x - 150, y - 60, x + 150, y + 60), fill=(255, 205, 50), outline=(255, 235, 140), width=6)
        d.text((x, y), "FC", font=font("Anton-Regular.ttf", 70), fill=(150, 100, 0), anchor="mm")
    return _glow(im, (255, 200, 0))


def draw_pack():
    from fmm.brand import font, LOGO
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((210, 90, 590, 710), 30, fill=(40, 10, 70), outline=(255, 215, 0), width=12)
    d.polygon([(210, 160), (590, 160), (590, 190), (210, 190)], fill=(255, 215, 0))
    d.text((400, 420), "PACK", font=font("Anton-Regular.ttf", 130), fill=(255, 215, 0), anchor="mm")
    return _glow(im, (138, 43, 226))


DRAW = {"gems": draw_gems, "mls": draw_mls, "player": draw_player, "draft": draw_draft, "coins": draw_coins, "pack": draw_pack}


def kind_of(reward):
    r = reward.lower()
    for kw, kind in KEYWORDS:
        if kw in r:
            return kind
    return "pack"


def pick(reward):
    kind = kind_of(reward)
    ovr = ovr_label(reward)
    if kind in ("mls", "player") and ovr and not (DIR / f"{kind}.png").exists():
        # card with the exact OVR range from the reward text
        out = GEN / f"{kind}_{ovr}.png"
        if not out.exists():
            GEN.mkdir(parents=True, exist_ok=True)
            (draw_mls if kind == "mls" else draw_player)(ovr).save(out)
        return str(out)
    for folder in (DIR, REAL):
        for ext in (".png", ".jpg", ".webp"):
            own = folder / f"{kind}{ext}"
            if own.exists():
                return str(own)
    gen = GEN / f"{kind}.png"
    if kind not in DRAW:
        gen = GEN / "pack.png"
    if not gen.exists():
        build()
    return str(gen)


def build():
    GEN.mkdir(parents=True, exist_ok=True)
    for k, fn in DRAW.items():
        fn().save(GEN / f"{k}.png")


if __name__ == "__main__":
    build()
    print("drew", sorted(p.name for p in GEN.glob("*.png")))
