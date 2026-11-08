"""FMM branded post generator — follows FMM Typography & Color Palette Guide.

Usage:  python -m fmm.brand content/sample_week.json
Each post in the JSON becomes a 1080x1350 PNG in output/.
"""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

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
    while size > 40 and max(d.textlength(w, font=f) for w in text.upper().split()) > max_w:
        size -= 4  # shrink until the longest single word fits (e.g. SCHWEINSTEIGER)
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


def _box(d, xy, fill=(16, 16, 22), outline=(48, 48, 60)):
    d.rounded_rectangle(xy, 18, fill=fill, outline=outline, width=2)


def ps_name(raw):
    """'PLAYSTYLE_INCISIVE_THROUGH_1' -> 'Incisive Through' (forum and RenderZ give raw codes)."""
    import re as _re
    return _re.sub(r"\s+\d+$", "", str(raw).replace("PLAYSTYLE_", "").replace("Playstyle ", "").replace("_", " ")).strip().title()


def post_review(p):
    """Card review (Design Playbook): big card, surname huge, 3 pros, one big verdict stamp, 6 face-stat tiles,
    playstyles + weak foot/skills as one line. Full detail is in the caption and the Reel. Falls back without p['info']."""
    info = p.get("info")
    if not info:
        return _post_review_plain(p)
    from fmm.review import face_stats
    img, d, c = base("review", p.get("background"))
    anton = lambda s: font("Anton-Regular.ttf", s)
    d.text((W - 60, 60), "NEW CARD REVIEW", font=label_font(30), fill=GOLD, anchor="ra")
    card = player_card({"name": p["player"], "card": p.get("card"), "tier": "gold", "ovr": info.get("ovr"),
                        "pos": info.get("pos")}, 460, 640)
    img.paste(card, (30 - 30, 150 - 30), card)
    d = ImageDraw.Draw(img)
    x0 = 530
    name = surname(p["player"])
    nf = anton(120)
    while d.textlength(name, font=nf) > W - 60 - x0 and nf.size > 56:
        nf = anton(nf.size - 6)
    d.text((x0, 140), name, font=nf, fill=WHITE)
    d.text((x0, 300), f"{info.get('ovr')} OVR  •  {info.get('pos')}", font=label_font(40), fill=c)
    wf, sm = info.get("weak_foot"), info.get("skill_moves")
    extra = "  •  ".join(x for x in (f"WEAK FOOT {wf}/5" if wf else "", f"SKILLS {sm}/5" if sm else "") if x)
    if extra:
        d.text((x0, 360), extra, font=label_font(32), fill=GRAY)
    y = 430
    for pro in (p.get("pros") or [])[:3]:
        d.text((x0, y), f"+ {pro}", font=label_font(34), fill=WHITE)
        y += 56
    verdict, score = p.get("verdict") or "", p.get("score") or 0
    col = {"MUST BUY": GREEN, "WORTH IT": GREEN, "SITUATIONAL": GOLD, "SKIP": RED}.get(verdict, c)
    d.rounded_rectangle((x0, 630, W - 50, 790), 26, fill=col)
    vf = anton(62)
    txt = f"{score:g}/10  {verdict}"
    while d.textlength(txt, font=vf) > W - 50 - x0 - 40 and vf.size > 36:
        vf = anton(vf.size - 4)
    d.text(((x0 + W - 50) // 2, 710), txt, font=vf, fill=BLACK, anchor="mm")
    fs = face_stats(info)
    bw, gap, y = 145, 14, 860
    for i, (k, v) in enumerate(fs.items()):
        bx = 60 + i * (bw + gap)
        _box(d, (bx, y, bx + bw, y + 170), outline=GREEN if v >= 150 else GOLD if v >= 130 else (60, 60, 70))
        d.text((bx + bw / 2, y + 72), str(v), font=anton(72), fill=WHITE, anchor="mm")
        d.text((bx + bw / 2, y + 140), k, font=label_font(30), fill=GRAY, anchor="mm")
    pss = [ps_name(x) for x in (info.get("playstyles") or [])][:3]
    if pss:
        d.text((60, 1080), "PLAYSTYLES:  " + "  •  ".join(x.upper() for x in pss), font=label_font(28), fill=PURPLE)
    return img


def _post_review_plain(p):
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


def surname(name):
    """Last name for big labels; 'Vini Jr.' -> 'VINI JR.' instead of 'JR.'."""
    w = (name or "").split()
    return (" ".join(w[-2:]) if len(w) > 1 and w[-1].rstrip(".").lower() in ("jr", "junior") else (w[-1] if w else "")).upper()


def post_top10(p):
    """Top 10: the #1 card big on the left (focal point), ranks 2-10 as readable rows (Design Playbook)."""
    img, d, c = base("top10", p.get("background"))
    anton = lambda s: font("Anton-Regular.ttf", s)
    title = f"TOP 10 {p['position'].upper()} {p.get('title', '').upper()}".strip()
    f = anton(80)
    while d.textlength(title, font=f) > W - 330 and f.size > 44:
        f = anton(f.size - 4)
    d.text((W // 2 + 110, 58), title, font=f, fill=WHITE, anchor="ma")
    players = p["players"][:10]
    val = lambda pl: pl.get("stat") or f"{pl.get('ovr', '')} OVR"
    hero = {"pos": p["position"], **players[0]}
    card = player_card(hero, 400, 560)
    img.paste(card, (40 - 30, 270 - 30), card)
    d = ImageDraw.Draw(img)
    d.text((250, 215), "#1", font=anton(110), fill=GOLD, anchor="mm", stroke_width=5, stroke_fill=BLACK)
    d.text((250, 880), val(hero), font=anton(60), fill=GOLD, anchor="mm")
    d.text((250, 950), surname(hero.get("name")), font=label_font(38), fill=WHITE, anchor="mm")
    y = 200
    for i, pl in enumerate(players[1:], 2):
        d.rounded_rectangle((480, y, W - 40, y + 84), 14, fill=(18, 18, 30) if i % 2 else (30, 30, 48))
        d.text((515, y + 42), str(i), font=anton(50), fill=GOLD if i <= 3 else WHITE, anchor="mm")
        if pl.get("card") and Path(pl["card"]).exists():
            th = fit_card(pl["card"], 56, 76)
            img.paste(th, (550 - 30, y + 4 - 30), th)
            d = ImageDraw.Draw(img)
        name, nf = surname(pl.get("name")), label_font(34)
        while d.textlength(name, font=nf) > 250 and nf.size > 22:
            nf = label_font(nf.size - 2)
        d.text((625, y + 42), name, font=nf, fill=WHITE, anchor="lm")
        d.text((W - 60, y + 42), str(pl.get("stat") or pl.get("ovr", "")).split()[-1], font=anton(46), fill=GOLD, anchor="rm")
        y += 94
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


def post_guess(p):
    """Guess the player: card blacked out, only OVR/position/hints visible."""
    img, d, c = base("poll", p.get("background"))
    d.text((W // 2, 190), "GUESS THE PLAYER", font=font("Anton-Regular.ttf", 110), fill=GOLD, anchor="ma",
           stroke_width=3, stroke_fill=(5, 5, 5))
    card = load_card(p["card"])
    s = 760 / card.height
    card = card.resize((int(card.width * s), 760), Image.LANCZOS)
    sil = Image.new("RGBA", card.size, (12, 12, 16, 255))
    sil.putalpha(card.getchannel("A"))
    glow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    glow.paste(Image.new("RGBA", card.size, PURPLE + (200,)), (0, 0), card)
    x, y = (W - card.width) // 2, 340
    g = glow.filter(ImageFilter.GaussianBlur(30))
    img.paste(g, (x, y), g)
    img.paste(sil, (x, y), sil)
    d = ImageDraw.Draw(img)
    d.text((W // 2, y + 380), "?", font=font("Anton-Regular.ttf", 300), fill=WHITE, anchor="mm")
    hints = p.get("hints", [])
    d.text((W // 2, 1140), "  •  ".join(hints).upper(), font=label_font(40), fill=WHITE, anchor="ma")
    footer(d, "COMMENT YOUR ANSWER • REVEALED IN OUR NEXT POST")
    return img


def post_rate(p):
    """Rate this card 1-10: big card + a 1..10 scale."""
    img, d, c = base("review", p.get("background"))
    d.text((W // 2, 190), "RATE THIS CARD", font=font("Anton-Regular.ttf", 110), fill=WHITE, anchor="ma",
           stroke_width=3, stroke_fill=RED)
    card = fit_card(p["card"], 560, 760, GOLD)
    img.paste(card, ((W - card.width) // 2, 320), card)
    d = ImageDraw.Draw(img)
    x0, y0, w = 90, 1140, (W - 180) / 10
    for i in range(10):
        col = tuple(int(RED[k] + (GREEN[k] - RED[k]) * i / 9) for k in range(3))
        d.rounded_rectangle((x0 + i * w + 4, y0, x0 + (i + 1) * w - 4, y0 + 90), 16, fill=col)
        d.text((x0 + i * w + w / 2, y0 + 45), str(i + 1), font=font("Anton-Regular.ttf", 56), fill=WHITE, anchor="mm")
    footer(d, "DROP YOUR RATING IN THE COMMENTS")
    return img


def _card_or_frame(p, cw, ch):
    """Real card image when we have it, otherwise the FMM framed card."""
    if p.get("card") and Path(p["card"]).exists():
        return fit_card(p["card"], cw, ch, None)
    pc = player_card({"name": p.get("name", "?"), "ovr": p.get("ovr", ""), "pos": p.get("pos", ""),
                      "tier": "silver"}, cw - 30, ch - 42)
    return pc.resize((cw + 60, ch + 60), Image.LANCZOS)  # same footprint as fit_card (30px glow margin)


def post_xi_part(p):
    """One line of the Budget XI: up to 3 big cards filling the frame (2 top, 1 bottom-centre), a price pill
    under each (Design Playbook: no empty middle). Bottom-right stays free for the ATB badge."""
    img, d, c = base("squad", p.get("background"))
    d.text((W // 2 + 90, 48), p.get("title", "BEST BUDGET XI").upper(), font=font("Anton-Regular.ttf", 84), fill=GOLD,
           anchor="ma", stroke_width=3, stroke_fill=(5, 5, 5))
    d.text((W // 2 + 90, 155), p.get("subtitle", "").upper(), font=label_font(32), fill=WHITE, anchor="ma")
    pl = p["players"]
    if len(pl) > 3:  # 4 defenders: 2 x 2
        spots = [(270, 400), (810, 400), (270, 870), (810, 870)]
        cw, ch = 300, 400
    else:
        spots = [(270, 470), (810, 470), (540, 960)][:len(pl)] if len(pl) > 1 else [(540, 640)]
        cw, ch = (340, 470) if len(pl) > 1 else (460, 640)
    for q, (x, y) in zip(pl, spots):
        card = _card_or_frame(q, cw, ch)
        img.paste(card, (int(x - card.width / 2), int(y - card.height / 2)), card)
        d = ImageDraw.Draw(img)
        txt, f = f"{q['shards']:,} SHARDS", font("Anton-Regular.ttf", 36)
        tw = d.textlength(txt, font=f)
        ty = y + ch / 2 + 8
        d.rounded_rectangle((x - tw / 2 - 20, ty, x + tw / 2 + 20, ty + 54), 27, fill=GOLD)
        d.text((x, ty + 27), txt, font=f, fill=BLACK, anchor="mm")
    return img


def post_xi(p):
    """Best XI on a pitch (4-3-3). p['players'] = 11 dicts in order GK, LB, CB, CB, RB, CM, CM, CM, LW, ST, RW."""
    img, d, c = base("squad", p.get("background"))
    d.text((W // 2 + 60, 60), p.get("title", "BEST BUDGET XI").upper(), font=font("Anton-Regular.ttf", 100), fill=GOLD,
           anchor="ma", stroke_width=3, stroke_fill=(5, 5, 5))
    if p.get("subtitle"):
        d.text((W // 2 + 60, 190), p["subtitle"].upper(), font=label_font(34), fill=WHITE, anchor="ma")
    # pitch
    pitch = (60, 250, W - 60, H - 90)
    d.rounded_rectangle(pitch, 30, fill=(18, 90, 40), outline=(255, 255, 255), width=4)
    for i in range(1, 8, 2):
        y0 = pitch[1] + (pitch[3] - pitch[1]) * i / 8
        d.rectangle((pitch[0] + 4, y0, pitch[2] - 4, y0 + (pitch[3] - pitch[1]) / 8), fill=(22, 104, 48))
    mx, my = W // 2, (pitch[1] + pitch[3]) // 2
    d.line((pitch[0], my, pitch[2], my), fill=(255, 255, 255), width=3)
    d.ellipse((mx - 110, my - 110, mx + 110, my + 110), outline=(255, 255, 255), width=3)
    d.rectangle((mx - 220, pitch[3] - 150, mx + 220, pitch[3]), outline=(255, 255, 255), width=3)
    d.rectangle((mx - 220, pitch[1], mx + 220, pitch[1] + 150), outline=(255, 255, 255), width=3)
    rows = [(0.86, [0.5]), (0.66, [0.14, 0.38, 0.62, 0.86]), (0.44, [0.22, 0.5, 0.78]), (0.2, [0.18, 0.5, 0.82])]
    pl, k = p["players"], 0
    cw, ch = 170, 238
    for fy, xs in rows:
        for fx in xs:
            if k >= len(pl):
                break
            x = pitch[0] + (pitch[2] - pitch[0]) * fx
            y = pitch[1] + (pitch[3] - pitch[1]) * fy
            card = _card_or_frame(pl[k], cw, ch)
            img.paste(card, (int(x - card.width / 2), int(y - card.height / 2)), card)
            if pl[k].get("shards"):  # Star Shards price pill just under the visible card art
                box = card.getchannel("A").getbbox() if card.mode == "RGBA" else None
                ty = y - card.height / 2 + (box[3] if box else card.height) + 2
                txt, f = f"{pl[k]['shards']:,} SHARDS", label_font(22)
                tw = d.textlength(txt, font=f)
                d.rounded_rectangle((x - tw / 2 - 10, ty, x + tw / 2 + 10, ty + 32), 14, fill=(5, 5, 5))
                d.text((x, ty + 4), txt, font=f, fill=GOLD, anchor="ma")
            k += 1
    return img


def post_gem(p):
    """Hidden gem: big card + its 4 best stats as bars."""
    img, d, c = base("event", p.get("background"))
    d.text((W // 2, 180), "HIDDEN GEM 💎".replace(" 💎", ""), font=font("Anton-Regular.ttf", 130), fill=(0, 230, 255),
           anchor="ma", stroke_width=4, stroke_fill=(5, 5, 5))
    d.text((W // 2, 335), p.get("subtitle", "").upper(), font=label_font(38), fill=WHITE, anchor="ma")
    card = fit_card(p["card"], 470, 650, (0, 200, 255))
    img.paste(card, (40, 410), card)
    x0, y = 600, 470
    for label, val in p.get("stats", [])[:5]:
        d.text((x0, y), label.upper(), font=label_font(32), fill=GRAY)
        bw = int(400 * min(1, val / 170))
        d.rounded_rectangle((x0, y + 46, x0 + 400, y + 82), 18, fill=(40, 40, 50))
        d.rounded_rectangle((x0, y + 46, x0 + bw, y + 82), 18, fill=GREEN)
        d.text((x0 + 400, y), str(val), font=font("Anton-Regular.ttf", 44), fill=WHITE, anchor="ra")
        y += 120
    d.text((W // 2, 1120), p.get("tagline", "LOW OVR. ELITE STATS.").upper(), font=title_font(64), fill=GOLD, anchor="ma")
    footer(d, "WOULD YOU USE HIM? TELL US 👇".replace(" 👇", ""))
    return img


def post_worth(p):
    """Is the event worth it? Top event cards in a row + FMM verdict stamp."""
    img, d, c = base("event", p.get("background"))
    d.text((W // 2, 170), f"IS {p['event']}".upper(), font=font("Anton-Regular.ttf", 110), fill=WHITE, anchor="ma",
           stroke_width=3, stroke_fill=PURPLE)
    d.text((W // 2, 300), "WORTH IT?", font=font("Anton-Regular.ttf", 140), fill=GOLD, anchor="ma",
           stroke_width=4, stroke_fill=(5, 5, 5))
    cards = p["cards"][:5]
    cw = 300 if len(cards) <= 3 else 200
    ch = int(cw * 1.4)
    gap = (W - len(cards) * cw) // (len(cards) + 1)
    for i, cd in enumerate(cards):
        card = fit_card(cd, cw, ch, GOLD)
        img.paste(card, (gap + i * (cw + gap) - 30, 520), card)
    d = ImageDraw.Draw(img)
    col = {"WORTH IT": GREEN, "MUST BUY": GREEN, "SITUATIONAL": (255, 152, 0)}.get(p["verdict"], RED)
    d.rounded_rectangle((180, 1000, W - 180, 1150), 30, fill=(10, 10, 10), outline=col, width=8)
    d.text((W // 2, 1075), f"FMM: {p['verdict']}", font=font("Anton-Regular.ttf", 90), fill=col, anchor="mm")
    d.text((W // 2, 1190), p.get("note", ""), font=caption_font(34), fill=GRAY, anchor="ma")
    footer(d, "ARE YOU SPENDING ON THIS EVENT?")
    return img


def post_meme(p):
    """Two-panel meme: top text + card, bottom text + card (greyed for the 'reality' panel)."""
    img, d, c = base("news", p.get("background"))
    panel_h = 560
    for i, (txt, cd, sad) in enumerate([(p["top"], p["card"], False), (p["bottom"], p.get("card2") or p["card"], True)]):
        y0 = 130 + i * (panel_h + 40)
        d.rounded_rectangle((50, y0, W - 50, y0 + panel_h), 30, fill=(250, 250, 250) if not sad else (30, 30, 34))
        lines = wrap(d, txt, title_font(58), 520)
        ty = y0 + panel_h / 2 - len(lines) * 34
        for ln in lines:
            d.text((90, ty), ln, font=title_font(58), fill=(10, 10, 10) if not sad else WHITE); ty += 68
        card = load_card(cd)
        card.thumbnail((380, panel_h - 60))
        if sad:
            card = Image.merge("RGBA", (*[ImageEnhance.Brightness(card.convert("L")).enhance(0.8)] * 3, card.getchannel("A")))
        img.paste(card, (W - 90 - card.width, int(y0 + (panel_h - card.height) / 2)), card)
        em = Image.open(EMOJI / ("love.png" if not sad else "haha.png")).convert("RGBA").resize((110, 110))
        img.paste(em, (W - 150, y0 + 20), em)
        d = ImageDraw.Draw(img)
    footer(d, "WHO ELSE DOES THIS?")  # no "tag a friend": Meta demotes tag-bait
    return img


def _stars(n):
    return ("★" * int(n) + "☆" * (5 - int(n))) if isinstance(n, int) and 0 < n <= 5 else ""


def post_compare(p):
    """1 vs 1: background split in two colours, both cards big, giant VS, 6 face stats with the winner in gold
    (Design Playbook). Full detail stays in the caption."""
    from fmm.review import face_stats
    a, b = p["a"], p["b"]
    img = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 0), (W // 2 + 90, 0), (W // 2 - 90, H), (0, H)], fill=(110, 6, 28))
    d.polygon([(W // 2 + 90, 0), (W, 0), (W, H), (W // 2 - 90, H)], fill=(16, 44, 130))
    shade = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shade).rectangle((0, 700, W, H), fill=150)
    img = Image.composite(Image.new("RGB", (W, H), BLACK), img, shade.filter(ImageFilter.GaussianBlur(80)))
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255))
    logo.thumbnail((180, 90))
    img.paste(logo, (40, 30), logo)
    anton = lambda s: font("Anton-Regular.ttf", s)
    for pl, x in ((a, 40), (b, 600)):
        card = fit_card(pl["card"], 380, 520, GOLD)
        img.paste(card, (x - 30, 120 - 30), card)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).text((W // 2, 380), "VS", font=anton(220), fill=RED + (255,), anchor="mm")
    g = g.filter(ImageFilter.GaussianBlur(22))
    img.paste(g, (0, 0), g)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 380), "VS", font=anton(220), fill=WHITE, anchor="mm", stroke_width=5, stroke_fill=BLACK)
    for pl, x in ((a, 230), (b, 790)):
        d.text((x, 670), surname(pl["name"]), font=anton(54), fill=WHITE, anchor="mm")
        d.text((x, 720), f"{pl['ovr']} {pl['pos']}", font=label_font(30), fill=GOLD, anchor="mm")
    fa, fb = face_stats(a), face_stats(b)
    y = 780
    for k in fa:
        va, vb = fa[k], fb.get(k, 0)
        x1 = W - 60 if y < 1050 else W - 250  # last rows end left of the ATB badge
        d.rounded_rectangle((60, y, x1, y + 68), 14, fill=(8, 8, 12))
        d.text((170, y + 34), str(va), font=anton(54), fill=GOLD if va > vb else WHITE, anchor="mm")
        d.text(((60 + x1) // 2, y + 34), k, font=label_font(32), fill=GRAY, anchor="mm")
        d.text((x1 - 110, y + 34), str(vb), font=anton(54), fill=GOLD if vb > va else WHITE, anchor="mm")
        y += 80
    d.rectangle((0, H - 14, W, H), fill=RED)
    return img


def post_compare4(p):
    """Top 4 of one position: 4 cards on top, face-stat rows, best value per row highlighted."""
    from fmm.review import face_stats
    pl = p["players"][:4]
    img, d, c = base("comparison", p.get("background"))
    d.text((W // 2 + 60, 60), f"TOP {len(pl)} {p['position']}".upper(), font=font("Anton-Regular.ttf", 96), fill=GOLD,
           anchor="ma", stroke_width=3, stroke_fill=(5, 5, 5))
    d.text((W // 2 + 60, 175), "STATS COMPARISON", font=label_font(34), fill=WHITE, anchor="ma")
    colw = (W - 220) / len(pl)
    for i, x in enumerate(pl):
        card = fit_card(x["card"], 190, 266, GOLD)
        cx = 200 + colw * i + colw / 2
        img.paste(card, (int(cx - card.width / 2), 230), card)
    d = ImageDraw.Draw(img)
    faces = [face_stats(x) for x in pl]
    y = 530  # table ends above the ATB badge (bottom-right safe zone)
    for k in ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]:
        vals = [f[k] for f in faces]
        best = max(vals)
        d.rounded_rectangle((60, y, W - 60, y + 86), 18, fill=(18, 18, 24))
        d.rounded_rectangle((60, y, 190, y + 86), 18, fill=(40, 30, 70))
        d.text((125, y + 43), k, font=label_font(34), fill=WHITE, anchor="mm")
        for i, v in enumerate(vals):
            cx = 200 + colw * i + colw / 2
            if v == best:
                d.rounded_rectangle((cx - 70, y + 10, cx + 70, y + 76), 14, fill=(0, 120, 60))
            d.text((cx, y + 43), str(v), font=font("Anton-Regular.ttf", 50), fill=WHITE, anchor="mm")
        y += 96
    footer(d, "WHO'S THE BEST? COMMENT YOUR PICK")
    return img


def post_pick3(p):
    """Pick one: 3 tall card panels with a reaction under each (Love / Wow / Haha)."""
    img, d, c = base("event", p.get("background"))
    d.text((W // 2 + 60, 60), p.get("title", "PICK ONE").upper(), font=font("Anton-Regular.ttf", 84), fill=WHITE,
           anchor="ma", stroke_width=3, stroke_fill=PURPLE)
    if p.get("subtitle"):
        d.text((W // 2 + 60, 165), p["subtitle"].upper(), font=label_font(34), fill=GOLD, anchor="ma")
    cards = p["cards"][:3]
    pw, ph, gap = 310, 820, 25
    x0 = (W - (3 * pw + 2 * gap)) // 2
    reacts = ["love", "wow", "haha"]
    for i, cd in enumerate(cards):
        x = x0 + i * (pw + gap)
        src = load_card(cd).convert("RGBA")
        bg = src.resize((pw, int(src.height * pw / src.width)))
        bg = bg.resize((int(bg.width * ph / bg.height * 1.3), int(ph * 1.3))).crop((0, 0, pw, ph))
        bg = ImageEnhance.Brightness(bg.convert("RGB").filter(ImageFilter.GaussianBlur(14))).enhance(0.55)
        m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), 28, fill=255)
        img.paste(bg, (x, 240), m)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x, 240, x + pw - 1, 240 + ph - 1), 28, outline=GOLD, width=5)
        card = fit_card(cd, pw - 30, 470, GOLD)
        img.paste(card, (x + (pw - card.width) // 2, 300), card)
        em = Image.open(EMOJI / f"{reacts[i]}.png").convert("RGBA")
        em = em.resize((150, int(150 * em.height / em.width)), Image.LANCZOS)
        img.paste(em, (x + (pw - em.width) // 2, 240 + ph - em.height - 40), em)
    d = ImageDraw.Draw(img)
    footer(d, "WHICH ONE ARE YOU PICKING?")
    return img


def post_choose4(p):
    """Choose 1: four cards in a 2x2 grid, a big option number on each (ref: RkReddy community poll)."""
    img, d, c = base("event", p.get("background"))
    d.text((W // 2 + 60, 60), p.get("title", "CHOOSE 1").upper(), font=font("Anton-Regular.ttf", 96), fill=WHITE,
           anchor="ma", stroke_width=3, stroke_fill=PURPLE)
    d.text((W // 2 + 60, 180), p.get("subtitle", "").upper(), font=label_font(34), fill=GOLD, anchor="ma")
    for i, cd in enumerate(p["cards"][:4]):
        x, y = 300 + (i % 2) * 460, 240 + (i // 2) * 460  # bottom-right card stays clear of the ATB badge
        card = fit_card(cd, 300, 420, GOLD)
        img.paste(card, (int(x - card.width / 2), y), card)
        d.ellipse((x - 175, y + 10, x - 105, y + 80), fill=GOLD)
        d.text((x - 140, y + 45), str(i + 1), font=font("Anton-Regular.ttf", 52), fill=(5, 5, 5), anchor="mm")
    footer(d, "COMMENT 1, 2, 3 OR 4")
    return img


TEMPLATES = {"choose4": post_choose4, "compare": post_compare, "compare4": post_compare4, "pick3": post_pick3, "xi": post_xi, "xi_part": post_xi_part, "gem": post_gem, "worth": post_worth, "meme": post_meme, "guess": post_guess, "rate": post_rate, "codes_list": post_codes_list, "code": post_code, "versus": post_versus, "spotlight": post_spotlight, "tip": post_tip, "tutorial": post_tip, "poll": post_poll, "review": post_review,
             "news": post_quote, "quote": post_quote, "event": post_quote, "pack": post_quote, "top10": post_top10}


def render(post, out_dir=OUT):
    out_dir.mkdir(parents=True, exist_ok=True)
    img = TEMPLATES[post["type"]](post)
    from fmm import atb
    img = atb.add_badge(img, post["id"])  # owner rule: a small ATB photo on every photo post
    path = out_dir / f"{post['id']}.png"
    img.save(path, quality=95)
    return path


if __name__ == "__main__":
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    for post in data["posts"]:
        print("made", render(post))
