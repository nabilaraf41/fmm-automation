"""FMM branded post generator — follows FMM Typography & Color Palette Guide.

Usage:  python -m fmm.brand content/sample_week.json
Each post in the JSON becomes a 1080x1350 PNG in output/.
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
LOGO = ROOT / "assets" / "logos" / "logo_white.png"
OUT = ROOT / "output"
EMOJI = ROOT / "assets" / "emoji"
REACTIONS = ["love", "wow", "haha", "like"]  # Facebook reaction order for poll options

BLACK, RED, WHITE = (5, 5, 5), (225, 6, 44), (255, 255, 255)
PURPLE, GOLD, GRAY = (138, 43, 226), (255, 215, 0), (217, 217, 217)
BLUE, GREEN = (41, 121, 255), (0, 200, 83)
ACCENTS = {  # content type -> (primary glow, secondary glow) per palette guide
    "review": (RED, PURPLE), "comparison": (RED, PURPLE), "event": (PURPLE, GOLD),
    "pack": (GOLD, RED), "squad": (BLUE, WHITE), "news": (RED, WHITE),
    "tutorial": (BLUE, WHITE), "tip": (BLUE, RED), "poll": (RED, PURPLE), "top10": (BLUE, PURPLE),
}
W, H = 1080, 1350


def font(name, size, weight=None):
    f = ImageFont.truetype(str(FONTS / name), size)
    if weight:  # variable fonts
        try:
            f.set_variation_by_axes([weight] if "Spartan" in name else [32, weight])
        except Exception:
            pass
    return f


def title_font(size): return font("LeagueSpartan.ttf", size, 700)
def body_font(size): return font("Inter.ttf", size, 400)
def caption_font(size): return font("Poppins-Medium.ttf", size)
def label_font(size): return font("Poppins-SemiBold.ttf", size)


def wrap(draw, text, f, max_w):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=f) <= max_w:
            line = test
        else:
            lines.append(line); line = word
    if line: lines.append(line)
    return lines


def base(kind, bg_image=None, size=(W, H)):
    w, h = size
    img = Image.new("RGB", size, BLACK)
    if bg_image and Path(bg_image).exists():
        bg = Image.open(bg_image).convert("RGB")
        scale = max(w / bg.width, h / bg.height)
        bg = bg.resize((int(bg.width * scale), int(bg.height * scale)))
        bg = bg.crop(((bg.width - w) // 2, (bg.height - h) // 2, (bg.width + w) // 2, (bg.height + h) // 2))
        img = Image.blend(img, bg, 0.55)
    c1, c2 = ACCENTS.get(kind, (RED, PURPLE))
    glow = Image.new("RGB", size, (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-w * .4, h * .55, w * .6, h * 1.3), fill=c1)
    gd.ellipse((w * .5, -h * .3, w * 1.4, h * .45), fill=c2)
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    img = Image.blend(img, Image.composite(glow, img, Image.new("L", size, 255)), 0.45)
    d = ImageDraw.Draw(img)
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255))  # drop dark backing box
    logo.thumbnail((180, 90) if kind == "top10" else (240, 120))
    img.paste(logo, (48, 40), logo)  # logo top-left per Canva Layout Guide
    d.rectangle((0, h - 14, w, h), fill=c1)
    return img, d, c1


def footer(d, text="FC MOBILE MANIA • FOLLOW FOR DAILY FC MOBILE CONTENT", h=H):
    f = caption_font(26)
    d.text((W // 2, h - 60), text, font=f, fill=GRAY, anchor="mm")


def tag(d, text, color, y=190):
    f = label_font(30)
    tw = d.textlength(text.upper(), font=f)
    d.rounded_rectangle((60, y, 60 + tw + 48, y + 56), 28, fill=color)
    d.text((84, y + 28), text.upper(), font=f, fill=WHITE, anchor="lm")


def draw_title(d, text, y, size=96, max_w=W - 120):
    f = title_font(size)
    for ln in wrap(d, text.upper(), f, max_w):
        d.text((60, y), ln, font=f, fill=WHITE)
        y += int(size * 1.05)
    return y


def post_tip(p):
    img, d, c = base(p.get("type", "tip"), p.get("background"))
    tag(d, p.get("tag", "Pro Tip"), c)
    y = draw_title(d, p["title"], 290)
    y += 30
    f = body_font(40)
    for i, point in enumerate(p.get("points", []), 1):
        d.ellipse((60, y + 2, 112, y + 54), fill=c)
        d.text((86, y + 28), str(i), font=label_font(30), fill=WHITE, anchor="mm")
        for ln in wrap(d, point, f, W - 220):
            d.text((140, y), ln, font=f, fill=WHITE); y += 52
        y += 26
    footer(d)
    return img


def post_poll(p):
    img, d, c = base("poll", p.get("background"))
    tag(d, "Community Poll", c)
    y = draw_title(d, p["title"], 290, 88)
    opts = p.get("options", [])
    y = max(y + 40, 700)
    for i, opt in enumerate(opts[:4]):
        d.rounded_rectangle((60, y, W - 60, y + 110), 22, outline=c, width=4, fill=(20, 20, 20))
        d.text((100, y + 55), opt.upper(), font=title_font(50), fill=WHITE, anchor="lm")
        emo = Image.open(EMOJI / f"{REACTIONS[i]}.png")
        emo.thumbnail((76, 76))
        img.paste(emo, (W - 100 - emo.width, y + 55 - emo.height // 2), emo)
        y += 135
    footer(d, "COMMENT YOUR PICK AND WHY")
    return img


TIER_COLORS = {"gold": (GOLD, (140, 100, 0)), "purple": (PURPLE, (60, 10, 110)),
               "red": (RED, (100, 0, 20)), "blue": (BLUE, (10, 40, 110)), "silver": ((192, 192, 192), (70, 70, 80))}


def silhouette():
    """Player silhouette cut from the FMM logo — placeholder when no player photo is given."""
    logo = Image.open(LOGO).convert("L").crop((60, 85, 220, 340))
    mask = logo.point(lambda v: 255 if v > 150 else 0)
    out = Image.new("RGBA", logo.size, (255, 255, 255, 0))
    out.putalpha(mask)
    return out


def load_card(path):
    """Open a ready-made card image; make a plain white/light background transparent and trim it.
    Uses the cleaned HD version from <folder>_hd/<name>.png when fmm.clean has made one."""
    hd = Path(path).parent.with_name(Path(path).parent.name + "_hd") / (Path(path).stem + ".png")
    if hd.exists():
        im = Image.open(hd).convert("RGBA")
        return im.crop(im.getbbox())
    im = Image.open(path).convert("RGBA")
    corner = im.getpixel((2, 2))
    if min(corner[:3]) > 225:  # white background -> flood-fill it away from every corner
        for xy in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1)):
            ImageDraw.floodfill(im, xy, (0, 0, 0, 0), thresh=40)
    return im.crop(im.getbbox())


def fit_card(path, cw, ch, glow_color=None):
    """Ready-made card scaled into a cw x ch box, with the same 30px glow margin as player_card."""
    card = load_card(path)
    s = min(cw / card.width, ch / card.height)  # scale up or down to fill the box
    card = card.resize((int(card.width * s), int(card.height * s)), Image.LANCZOS)
    out = Image.new("RGBA", (cw + 60, ch + 60), (0, 0, 0, 0))
    x, y = 30 + (cw - card.width) // 2, 30 + (ch - card.height) // 2
    if glow_color:
        g = Image.new("RGBA", out.size, (0, 0, 0, 0))
        g.paste(Image.new("RGBA", card.size, glow_color + (170,)), (x, y), card)
        out = g.filter(ImageFilter.GaussianBlur(16))
    out.paste(card, (x, y), card)
    return out


def player_card(p, cw, ch):
    """FC-Mobile-style framed player card: tier-colored frame, photo, OVR, position, name plate.
    If p["card"] points to a ready-made card image (game screenshot), that is used instead."""
    if p.get("card") and Path(p["card"]).exists():
        return fit_card(p["card"], cw, ch, TIER_COLORS.get(p.get("tier", ""), (None,))[0])
    tier = p.get("tier", "gold")
    rim, deep = TIER_COLORS.get(tier, TIER_COLORS["gold"])
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    # inner background: vertical gradient deep -> black
    grad = Image.new("RGB", (1, ch))
    for yy in range(ch):
        t = yy / ch
        grad.putpixel((0, yy), tuple(int(deep[k] * (1 - t) + 10 * t) for k in range(3)))
    grad = grad.resize((cw, ch))
    mask = Image.new("L", (cw, ch), 0)
    r = max(12, cw // 14)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw - 1, ch - 1), r, fill=255)
    card.paste(grad, (0, 0), mask)
    # player photo (or silhouette), bottom-aligned in the upper area
    photo_box = (int(cw * .08), int(ch * .10), int(cw * .92), int(ch * .78))
    bw, bh = photo_box[2] - photo_box[0], photo_box[3] - photo_box[1]
    src = Image.open(p["image"]).convert("RGBA") if p.get("image") and Path(p["image"]).exists() else silhouette()
    scale = max(bw / src.width, bh / src.height) if p.get("image") else min(bw / src.width, bh / src.height) * .9
    src = src.resize((int(src.width * scale), int(src.height * scale)))
    if p.get("image"):
        src = src.crop(((src.width - bw) // 2, 0, (src.width + bw) // 2, bh))
    card.paste(src, (photo_box[0] + (bw - src.width) // 2, photo_box[3] - src.height), src)
    d = ImageDraw.Draw(card)
    # name plate
    plate_y = int(ch * .78)
    d.rectangle((r // 2, plate_y, cw - r // 2, ch - r), fill=(5, 5, 5, 230))
    d.line((cw * .12, plate_y, cw * .88, plate_y), fill=rim, width=max(2, cw // 90))
    name = p.get("name", "").upper()
    nf = title_font(max(16, cw // 9))
    while d.textlength(name, font=nf) > cw * .86 and nf.size > 12:
        nf = title_font(nf.size - 2)
    d.text((cw // 2, (plate_y + ch - r) // 2), name, font=nf, fill=WHITE, anchor="mm")
    # OVR + position, top-left
    d.text((int(cw * .09), int(ch * .05)), str(p.get("ovr", "")), font=font("Anton-Regular.ttf", cw // 5), fill=WHITE,
           stroke_width=max(1, cw // 120), stroke_fill=(0, 0, 0))
    d.text((int(cw * .10), int(ch * .05) + cw // 5 + cw // 30), p.get("pos", "").upper(), font=label_font(max(12, cw // 13)),
           fill=rim)
    # frame: outer rim + inner hairline
    fw = max(3, cw // 40)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), r, outline=rim, width=fw)
    d.rounded_rectangle((fw * 2, fw * 2, cw - 1 - fw * 2, ch - 1 - fw * 2), max(4, r - fw * 2), outline=(255, 255, 255, 90), width=1)
    # soft outer glow
    glow = Image.new("RGBA", (cw + 60, ch + 60), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((30, 30, cw + 29, ch + 29), r, fill=rim + (150,))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    glow.paste(card, (30, 30), card)
    return glow  # note: includes 30px glow margin on each side


def post_review(p):
    img, d, c = base("review", p.get("background"))
    tag(d, p.get("tag", "Player Review"), c)
    card = player_card({"name": p["player"], "ovr": p.get("ovr"), "pos": p.get("pos", ""), "image": p.get("image"),
                        "tier": p.get("tier", "gold"), "card": p.get("card")}, 400, 560)
    img.paste(card, (W - 60 - 400 - 30, 280 - 30), card)
    y = draw_title(d, p["player"], 290, 84, max_w=W - 560)
    for ln in wrap(d, p.get("subtitle", ""), caption_font(34), W - 560):
        d.text((60, y + 5), ln, font=caption_font(34), fill=GRAY); y += 46
    y = 880
    col_x = [60, W // 2 + 20]
    for (label, items, colr), x in zip((("STRENGTHS", p.get("pros", []), GREEN), ("WEAKNESSES", p.get("cons", []), RED)), col_x):
        yy = y
        d.text((x, yy), label, font=label_font(34), fill=colr); yy += 56
        for it in items:
            for k, ln in enumerate(wrap(d, it, body_font(34), W // 2 - 110)):
                d.text((x, yy), ("•  " if k == 0 else "    ") + ln, font=body_font(34), fill=WHITE); yy += 46
    score = p.get("score")
    if score:
        d.rounded_rectangle((W - 330, H - 260, W - 60, H - 110), 24, fill=c)
        d.text((W - 195, H - 205), f"{score}/10", font=title_font(70), fill=WHITE, anchor="mm")
        d.text((W - 195, H - 140), "FMM RATING", font=label_font(24), fill=WHITE, anchor="mm")
    footer(d)
    return img


def post_quote(p):
    img, d, c = base(p.get("type", "news"), p.get("background"))
    tag(d, p.get("tag", "FMM"), c)
    f = title_font(84)
    lines = wrap(d, p["title"].upper(), f, W - 140)
    y = (H - len(lines) * 90) // 2
    for ln in lines:
        d.text((W // 2, y), ln, font=f, fill=WHITE, anchor="ma"); y += 90
    if p.get("subtitle"):
        d.text((W // 2, y + 40), p["subtitle"], font=caption_font(38), fill=GRAY, anchor="ma")
    footer(d)
    return img


def post_top10(p):
    """Top 10 rankings for one position, 3-4-3 card grid (reference: Top 10 CDM Rankings)."""
    img, d, c = base("top10", p.get("background"))
    d.text((W // 2 + 60, 58), f"TOP 10 {p['position'].upper()}", font=title_font(58), fill=WHITE, anchor="ma")
    d.text((W // 2 + 60, 122), p.get("title", "RANKINGS").upper(), font=title_font(104), fill=WHITE, anchor="ma",
           stroke_width=3, stroke_fill=BLUE)
    players = p["players"][:10]
    cw, ch, gap = 210, 290, 30
    rows = [(0, 3, 295), (3, 7, 650), (7, 10, 1005)]
    for start, end, cy in rows:
        n = end - start
        x0 = (W - (n * cw + (n - 1) * gap)) // 2
        for k, pl in enumerate(players[start:end]):
            rank = start + k + 1
            x = x0 + k * (cw + gap)
            pl = {"pos": p["position"], **pl}
            card = player_card(pl, cw, ch)
            img.paste(card, (x - 30, cy - 30), card)
            d.text((x + cw // 2, cy - 8), str(rank), font=font("Anton-Regular.ttf", 64),
                   fill=GOLD if rank <= 3 else WHITE, anchor="mb", stroke_width=3, stroke_fill=(5, 5, 5))
    return img


def post_code(p):
    """Redeem code announcement: NEW CODE, reward visual, big copyable code box."""
    img, d, c = base("pack", p.get("background"))
    d.text((W // 2, 200), p.get("title", "NEW CODE!!").upper(), font=title_font(110), fill=GOLD, anchor="ma",
           stroke_width=3, stroke_fill=(5, 5, 5))
    if p.get("subtitle"):
        d.text((W // 2, 325), p["subtitle"], font=caption_font(38), fill=GRAY, anchor="ma")
    if p.get("reward_image") and Path(p["reward_image"]).exists():
        card = fit_card(p["reward_image"], 420, 480, GOLD)
        img.paste(card, ((W - card.width) // 2, 390 - 30), card)
    else:  # no visual: big gift badge
        d.ellipse((W // 2 - 190, 440, W // 2 + 190, 820), fill=(25, 20, 5), outline=GOLD, width=8)
        d.text((W // 2, 630), "FREE", font=font("Anton-Regular.ttf", 130), fill=GOLD, anchor="mm")
    d.text((W // 2, 900), "CODE IS:", font=title_font(64), fill=WHITE, anchor="ma")
    code = p["code"].upper()
    cf = font("Anton-Regular.ttf", 120)
    tw = d.textlength(code, font=cf)
    bx0, bx1 = (W - tw) // 2 - 60, (W + tw) // 2 + 60
    d.rounded_rectangle((bx0, 990, bx1, 1170), 28, fill=(15, 15, 15), outline=GOLD, width=5)
    d.text((W // 2, 1080), code, font=cf, fill=WHITE, anchor="mm")
    d.text((W // 2, 1200), p.get("note", "Redeem at redeem.fcm.ea.com"), font=caption_font(34),
           fill=GRAY, anchor="ma")
    footer(d, "FOLLOW FMM SO YOU NEVER MISS A CODE")
    return img


def post_spotlight(p):
    """Hero spotlight: big title, large cut-out player, angled accent beams, card bottom-right."""
    rim = TIER_COLORS.get(p.get("tier", "gold"), TIER_COLORS["gold"])[0]
    img, d, c = base("event", p.get("background"))
    beams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beams)
    bd.polygon([(0, 900), (W, 560), (W, 640), (0, 980)], fill=rim + (150,))
    bd.polygon([(0, 1010), (W, 700), (W, 720), (0, 1030)], fill=rim + (90,))
    img.paste(beams, (0, 0), beams)
    if p.get("hero") and Path(p["hero"]).exists():  # cut-out player photo from fmm.clean
        hero = Image.open(p["hero"]).convert("RGBA")
        s = 1080 / hero.height
        hero = hero.resize((int(hero.width * s), int(hero.height * s)), Image.LANCZOS)
        shadow = Image.new("RGBA", hero.size, (0, 0, 0, 0))
        shadow.paste(Image.new("RGBA", hero.size, rim + (120,)), (0, 0), hero)
        shadow = shadow.filter(ImageFilter.GaussianBlur(25))
        hx = max(-80, (W - hero.width) // 2 - 160)
        img.paste(shadow, (hx, H - hero.height), shadow)
        img.paste(hero, (hx, H - hero.height), hero)
    d = ImageDraw.Draw(img)
    d.text((W // 2 + 60, 40), p.get("title", "ICONS").upper(), font=font("Anton-Regular.ttf", 150), fill=WHITE,
           anchor="ma", stroke_width=4, stroke_fill=rim)
    if p.get("subtitle"):
        d.text((W // 2 + 60, 235), p["subtitle"].upper(), font=label_font(36), fill=rim, anchor="ma")
    if p.get("card"):
        card = fit_card(p["card"], 360, 500, rim).rotate(-4, resample=Image.BICUBIC, expand=True)
        img.paste(card, (W - card.width + 10, H - card.height - 40), card)
    d.text((60, H - 150), p.get("player", "").upper(), font=title_font(70), fill=WHITE,
           stroke_width=2, stroke_fill=(5, 5, 5))
    d.text((60, H - 70), "FC MOBILE MANIA", font=label_font(30), fill=rim)
    return img


def slanted_text(img, text, cx, y, size, fill=WHITE, glow=BLUE, max_w=W - 120):
    """Bold italic-style headline: League Spartan sheared to slant forward, with a soft glow."""
    f = title_font(size)
    d0 = ImageDraw.Draw(img)
    lines = wrap(d0, text.upper(), f, max_w)
    lh = int(size * 1.05)
    layer = Image.new("RGBA", (W, lh * len(lines) + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        ld.text((cx, 20 + i * lh), ln, font=f, fill=fill, anchor="ma", stroke_width=3, stroke_fill=glow)
    layer = layer.transform(layer.size, Image.AFFINE, (1, 0.22, -0.22 * layer.height / 2, 0, 1, 0), Image.BICUBIC)
    halo = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    halo.paste(Image.new("RGBA", layer.size, glow + (200,)), (0, 0), layer)
    halo = halo.filter(ImageFilter.GaussianBlur(14))
    img.paste(halo, (0, y), halo)
    img.paste(layer, (0, y), layer)


def post_versus(p):
    """Reaction battle: 2-4 cards, each with a Facebook reaction above it, slanted question below."""
    img, d, c = base(p.get("theme", "tip"), p.get("background"))
    if p.get("tag"):
        d.text((W // 2 + 60, 80), p["tag"].upper(), font=label_font(34), fill=GRAY, anchor="ma")
    cards = p["cards"][:4]
    n = len(cards)
    cw = {2: 400, 3: 320, 4: 240}[n]
    ch = int(cw * 1.4)
    gap = (W - n * cw) // (n + 1)
    react = p.get("reactions", ["wow", "love", "haha", "like"][:n])
    top = 360 if n == 2 else 400
    for i, cd in enumerate(cards):
        x = gap + i * (cw + gap)
        emo = Image.open(EMOJI / f"{react[i]}.png")
        e = 96 if n == 2 else 80
        emo = emo.resize((int(emo.width * e / emo.height), e), Image.LANCZOS)
        img.paste(emo, (x + (cw - emo.width) // 2, top - e - 30), emo)
        card = player_card(cd, cw, ch)
        img.paste(card, (x - 30, top - 30), card)
    slanted_text(img, p["title"], W // 2, top + ch + 70, 104 if n == 2 else 92)
    footer(d, p.get("footer", "WHICH ONE WOULD YOU PICK? TELL US WHY"))  # no "react to vote": Meta demotes vote-bait
    return img


def post_codes_list(p):
    """Daily roundup of every active redeem code."""
    img, d, c = base("pack", p.get("background"))
    d.text((W // 2, 190), "ACTIVE CODES", font=font("Anton-Regular.ttf", 120), fill=GOLD, anchor="ma",
           stroke_width=3, stroke_fill=(5, 5, 5))
    d.text((W // 2, 345), p.get("date", __import__("datetime").date.today().strftime("%d %B %Y")).upper(),
           font=label_font(36), fill=GRAY, anchor="ma")
    codes = p["codes"][:6]
    row = min(220, 760 // max(1, len(codes)))
    y = 440 + (760 - row * len(codes)) // 2  # center the list in the free space
    for cd in codes:
        d.rounded_rectangle((60, y, W - 60, y + row - 20), 24, fill=(18, 18, 18), outline=GOLD, width=3)
        cf = font("Anton-Regular.ttf", int(row * 0.42))
        d.text((100, y + (row - 20) / 2), cd["code"], font=cf, fill=WHITE, anchor="lm")
        rf = caption_font(28)
        reward = cd.get("reward", "")
        while d.textlength(reward, font=rf) > 400 and len(reward) > 4:
            reward = reward[:-2]
        d.text((W - 100, y + (row - 20) / 2), reward if reward == cd.get("reward", "") else reward + "…", font=rf,
               fill=GOLD, anchor="rm")
        y += row
    d.text((W // 2, 1215), "Redeem at redeem.fcm.ea.com", font=caption_font(36), fill=GRAY, anchor="ma")
    footer(d, "FOLLOW FMM SO YOU NEVER MISS A CODE")
    return img


TEMPLATES = {"codes_list": post_codes_list, "code": post_code, "versus": post_versus, "spotlight": post_spotlight, "tip": post_tip, "tutorial": post_tip, "poll": post_poll, "review": post_review,
             "news": post_quote, "quote": post_quote, "event": post_quote, "pack": post_quote, "top10": post_top10}


def render(post, out_dir=OUT):
    out_dir.mkdir(parents=True, exist_ok=True)
    img = TEMPLATES[post["type"]](post)
    path = out_dir / f"{post['id']}.png"
    img.save(path, quality=95)
    return path


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for post in data["posts"]:
        print("made", render(post))
