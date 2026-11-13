"""Animated FMM Reels (1080x1920, 30fps) built from scenes.

Effect ideas adapted from github.com/Vibha-Ramprakash/claude-video-effects (MIT), rebuilt for
faceless card content in the FMM brand.

Usage:  python -m fmm.motion content/sample_reels.json      -> output/<id>.mp4
Each reel = list of scenes; every reel ends with the Follow outro unless "outro": false.

Scenes:
  reveal     card builds out of glowing dots, title slides in        {card, title, sub}
  countdown  Top 10 countdown with flip numbers, #1 dot-reveal         {position, players:[{card|name,ovr,tier}]}
  code       redeem code types itself into a comment bar              {code, card?}
  stamp      card + big stamp slams down                              {card, text, color?}
  messages   notification pop-ups stack up                            {title, lines:[...]}
  stat       glass graph climbs, number counts up                     {card?, label, from, to}
  swipe      before/after slider between two cards                    {before, after, title?}
  tierlist   players drop into S/A/B/C rows                           {title, tiers:{S:[cards],A:[...]}}
  outro      FMM logo + Follow button flips to Following              {}
"""
import json, math, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

from fmm.brand import (BLACK, RED, WHITE, PURPLE, GOLD, GRAY, BLUE, GREEN, LOGO, OUT, TIER_COLORS,
                       base, font, title_font, label_font, caption_font, body_font, load_card, player_card)

RW, RH, FPS = 1080, 1920, 30
ANTON = "Anton-Regular.ttf"


# ---------- easing / helpers ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x): x = clamp(x); s = 1.7; x -= 1; return x * x * ((s + 1) * x + s) + 1
def ease_inout(x): x = clamp(x); return 3 * x * x - 2 * x * x * x


_BG = {}
def background(kind):
    if kind not in _BG:
        img, _, _ = base(kind, None, (RW, RH))
        _BG[kind] = img.convert("RGBA")
    return _BG[kind].copy()


_CARDS = {}
def card_img(path, h):
    key = (path, h)
    if key not in _CARDS:
        im = load_card(path)
        _CARDS[key] = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return _CARDS[key]


def paste_center(frame, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def text_layer(s, f, fill=WHITE, stroke=0, stroke_fill=BLACK, glow=None):
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), s, font=f, stroke_width=stroke)
    pad = 40 if glow else 4
    im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - l, pad - t), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    if glow:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0))
        g.paste(Image.new("RGBA", im.size, glow + (220,)), (0, 0), im)
        g = g.filter(ImageFilter.GaussianBlur(16))
        g.alpha_composite(im)
        im = g
    return im


def glow_behind(im, color, blur=30, strength=170):
    g = Image.new("RGBA", (im.width + blur * 4, im.height + blur * 4), (0, 0, 0, 0))
    g.paste(Image.new("RGBA", im.size, color + (strength,)), (blur * 2, blur * 2), im)
    g = g.filter(ImageFilter.GaussianBlur(blur))
    g.alpha_composite(im, (blur * 2, blur * 2))
    return g


def logo_small(frame):
    """No-op: brand.base() already places the logo top-left. Kept so scenes read clearly."""


def headline(frame, s, y, size=96, color=WHITE, glow=BLUE, t=1.0):
    """Headline that slides up + fades in over t in [0,1]."""
    im = text_layer(s.upper(), title_font(size), color, 3, BLACK, glow)
    paste_center(frame, im, RW / 2, y + (1 - ease_out(t)) * 60, alpha=clamp(t * 1.5))


def dots_version(card, cell=18):
    """Glowing-dot rendering of a card (dot-reveal start state)."""
    small = card.resize((max(1, card.width // cell), max(1, card.height // cell)), Image.BILINEAR)
    out = Image.new("RGBA", card.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    for yy in range(small.height):
        for xx in range(small.width):
            r, g, b, a = small.getpixel((xx, yy))
            if a < 60:
                continue
            lum = (r + g + b) / 765
            rad = cell * (0.18 + 0.32 * lum)
            cx, cy = xx * cell + cell / 2, yy * cell + cell / 2
            d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(r, g, b, 255))
    return out.filter(ImageFilter.GaussianBlur(1))


_DOTS = {}
def dot_reveal(frame, path, h, cx, cy, t, color=GOLD):
    """t in [0,1]: dots grow in (0-.45), cross-fade to the real card (.45-.8), glow pulse."""
    card = card_img(path, h)
    key = (path, h)
    if key not in _DOTS:
        _DOTS[key] = dots_version(card)
    dots = _DOTS[key]
    if t < 0.8:
        paste_center(frame, dots, cx, cy, 0.85 + 0.15 * ease_out(t / 0.45), alpha=clamp(t / 0.25) * (1 - clamp((t - 0.55) / 0.25)))
    if t > 0.45:
        k = clamp((t - 0.45) / 0.35)
        paste_center(frame, glow_behind(card, color, 28, int(200 * k)), cx, cy, 0.9 + 0.1 * ease_back(k), alpha=k)


# ---------- scenes: each returns (duration, draw(frame, t_seconds)) ----------
def sc_reveal(s):
    dur = s.get("dur", 3.5)
    def draw(t):
        f = background(s.get("theme", "event"))
        logo_small(f)
        headline(f, s.get("title", "NEW CARD"), 230, 120, GOLD, RED, t / 0.5)
        if s.get("sub"):
            headline(f, s["sub"], 380, 48, WHITE, None, (t - 0.3) / 0.5)
        dot_reveal(f, s["card"], 1050, RW / 2, 1080, t / 2.0)
        sparkles(f, t, RW / 2, 1080, 470, 560, GOLD, clamp((t - 0.9) / 0.3))
        return shake(f, t, 1.0)
    return dur, draw


def sc_countdown(s):
    players = s["players"][:10]
    per, last = s.get("per", 1.1), s.get("last", 2.6)
    dur = 0.8 + per * (len(players) - 1) + last
    order = list(range(len(players)))[::-1]  # 10 -> 1

    def draw(t):
        f = background("top10")
        logo_small(f)
        headline(f, f"TOP {len(players)} {s['position'].upper()}", 220, 104, WHITE, BLUE, t / 0.5)
        if t < 0.8:
            return f
        lt = t - 0.8
        k = min(int(lt // per), len(players) - 1)
        idx = order[k]
        rank = idx + 1
        st = lt - k * per
        # flip number: squashes in on Y like a flip clock
        num = text_layer(f"#{rank}", font(ANTON, 230), GOLD if rank <= 3 else WHITE, 6, BLACK, GOLD if rank == 1 else None)
        sq = ease_out(st / 0.25)
        num = num.resize((num.width, max(1, int(num.height * sq))))
        paste_center(f, num, RW / 2, 470)
        p = players[idx]
        if rank == 1:
            dot_reveal(f, p["card"], 980, RW / 2, 1170, st / 1.6) if p.get("card") else None
        else:
            if p.get("card"):
                paste_center(f, glow_behind(card_img(p["card"], 900), TIER_COLORS.get(p.get("tier", "gold"))[0], 24, 150),
                             RW / 2, 1150, 0.6 + 0.4 * ease_back(st / 0.35), alpha=clamp(st / 0.15))
            else:
                c = player_card({"pos": s["position"], **p}, 560, 784)
                paste_center(f, c, RW / 2, 1150, 0.6 + 0.4 * ease_back(st / 0.35), alpha=clamp(st / 0.15))
        if p.get("name"):
            paste_center(f, text_layer(p["name"].upper(), title_font(70), WHITE, 3), RW / 2, 1700, alpha=clamp((st - 0.2) / 0.2))
        if rank == 1:
            sparkles(f, t, RW / 2, 1170, 460, 540, GOLD, clamp((st - 0.8) / 0.3))
            f = shake(f, st, 0.75)
        return f
    return dur, draw


def sc_code(s):
    code = s["code"].upper()
    dur = s.get("dur", 4.5)
    def draw(t):
        f = background("pack")
        logo_small(f)
        headline(f, s.get("title", "NEW CODE!!"), 230, 130, GOLD, RED, t / 0.4)
        if s.get("card"):
            paste_center(f, glow_behind(card_img(s["card"], 700), GOLD, 26, 150), RW / 2, 840,
                         0.7 + 0.3 * ease_back((t - 0.2) / 0.5), alpha=clamp((t - 0.2) / 0.3))
        # comment bar typing the code
        bx0, by0, bx1, by1 = 70, 1340, RW - 70, 1480
        bar = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        d = ImageDraw.Draw(bar)
        a = int(255 * clamp((t - 0.6) / 0.3))
        d.rounded_rectangle((bx0, by0, bx1, by1), 70, fill=(28, 28, 32, a), outline=(80, 80, 90, a), width=3)
        n = int(clamp((t - 1.0) / 1.4) * len(code))
        typed = code[:n] + ("|" if (t * 2) % 1 < 0.5 and n < len(code) else "")
        d.text((bx0 + 60, (by0 + by1) / 2), typed if n else "Add a comment...", font=font(ANTON, 76) if n else caption_font(40),
               fill=(255, 255, 255, a) if n else (140, 140, 150, a), anchor="lm")
        posted = t > 2.7
        d.text((bx1 - 50, (by0 + by1) / 2), "Post", font=label_font(40),
               fill=(GOLD if posted else (90, 140, 255)) + (a,), anchor="rm")
        f.alpha_composite(bar)
        if posted:
            k = ease_back((t - 2.7) / 0.35)
            pill = text_layer("COPY IT FAST  ✓".replace("  ✓", ""), label_font(46), BLACK)
            box = Image.new("RGBA", (pill.width + 80, pill.height + 40), (0, 0, 0, 0))
            ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), box.height // 2, fill=GREEN + (255,))
            box.alpha_composite(pill, (40, 20))
            paste_center(f, box, RW / 2, 1600, k)
            sparkles(f, t, RW / 2, 1410, 480, 140, GOLD, clamp((t - 2.75) / 0.3))
        if s.get("reward"):
            paste_center(f, text_layer(s["reward"], label_font(44), WHITE), RW / 2, 1240, alpha=clamp((t - 0.5) / 0.3))
        paste_center(f, text_layer("Redeem at redeem.fcm.ea.com", caption_font(40), GRAY), RW / 2, 1740, alpha=clamp((t - 3) / 0.3))
        return f
    return dur, draw


def stamp_img(text, color):
    tl = text_layer(text.upper(), font(ANTON, 170), color)
    box = Image.new("RGBA", (tl.width + 90, tl.height + 50), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    d.rounded_rectangle((6, 6, box.width - 7, box.height - 7), 24, outline=color + (255,), width=14)
    box.alpha_composite(tl, (45, 25))
    # grungy ink: knock out random specks
    import random
    rnd = random.Random(7)
    a = box.getchannel("A")
    ad = ImageDraw.Draw(a)
    for _ in range(260):
        x, y, r = rnd.randint(0, box.width), rnd.randint(0, box.height), rnd.randint(2, 7)
        ad.ellipse((x - r, y - r, x + r, y + r), fill=0)
    box.putalpha(a)
    return box


def sc_stamp(s):
    dur = s.get("dur", 3.2)
    col = tuple(s["color"]) if s.get("color") else RED
    st = stamp_img(s["text"], col)
    def draw(t):
        f = background(s.get("theme", "review"))
        logo_small(f)
        if s.get("title"):
            headline(f, s["title"], 230, 96, WHITE, RED, t / 0.4)
        paste_center(f, glow_behind(card_img(s["card"], 1050), GOLD, 24, 120), RW / 2, 1050, 0.92 + 0.08 * ease_out(t / 0.5),
                     alpha=clamp(t / 0.3))
        if t > 1.0:
            k = clamp((t - 1.0) / 0.18)
            shake = (1 - clamp((t - 1.18) / 0.3)) * 14 * math.sin(t * 90) if t > 1.18 else 0
            paste_center(f, st, RW / 2 + shake, 1100, 3.0 - 2.0 * ease_out(k), rot=-12, alpha=k)
        return f
    return dur, draw


def bubble(title, body, w=940):
    h = 190
    im = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 40, w + 30, h + 40), 44, fill=(0, 0, 0, 160))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((30, 30, w + 30, h + 30), 44, fill=(245, 243, 240, 245))
    icon = Image.open(LOGO).convert("RGBA").crop((40, 70, 240, 350)).resize((100, 140))
    tile = Image.new("RGBA", (120, 120), BLACK + (255,))
    tile.alpha_composite(icon.crop((0, 10, 100, 130)).resize((100, 120)), (10, 0))
    m = Image.new("L", (120, 120), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 119, 119), 28, fill=255)
    im.paste(tile, (60, 65), m)
    d.text((210, 72), title, font=label_font(36), fill=(20, 20, 20))
    d.text((w - 10, 76), "now", font=caption_font(30), fill=(130, 130, 130), anchor="ra")
    lines, line = [], ""
    for wd in body.split():
        tst = (line + " " + wd).strip()
        if d.textlength(tst, font=body_font(36)) < w - 230: line = tst
        else: lines.append(line); line = wd
    lines.append(line)
    for i, ln in enumerate(lines[:2]):
        d.text((210, 125 + i * 46), ln, font=body_font(36), fill=(40, 40, 40))
    return im


def sc_messages(s):
    lines = s["lines"][:5]
    gap = s.get("gap", 0.7)
    dur = s.get("dur", 1.0 + gap * len(lines) + 1.2)
    bubbles = [bubble(s.get("title", "FC Mobile Mania"), ln) for ln in lines]
    def draw(t):
        f = background(s.get("theme", "news"))
        logo_small(f)
        if s.get("headline"):
            headline(f, s["headline"], 240, 100, WHITE, RED, t / 0.4)
        top = 520
        for i, b in enumerate(bubbles):
            t0 = 0.6 + i * gap
            if t < t0:
                break
            k = ease_back((t - t0) / 0.35)
            paste_center(f, b, RW / 2, top + i * 250 + (1 - k) * 60, 0.85 + 0.15 * k, alpha=clamp((t - t0) / 0.2))
        return f
    return dur, draw


def num_parts(v):
    s = str(v); i = 0
    while i < len(s) and (s[i].isdigit() or s[i] == "."): i += 1
    return float(s[:i] or 0), s[i:]


def sc_stat(s):
    dur = s.get("dur", 3.6)
    a, suf = num_parts(s.get("from", 0)); b, _ = num_parts(s.get("to", 100))
    pts = [0.08, 0.18, 0.15, 0.32, 0.30, 0.48, 0.55, 0.70, 0.82, 1.0]
    def draw(t):
        f = background(s.get("theme", "squad"))
        logo_small(f)
        if s.get("title"):
            headline(f, s["title"], 220, 96, WHITE, BLUE, t / 0.4)
        if s.get("card"):
            paste_center(f, glow_behind(card_img(s["card"], 640), BLUE, 24, 140), RW / 2, 700, alpha=clamp(t / 0.3))
        # glass panel
        x0, y0, x1, y1 = 90, 1100, RW - 90, 1760
        region = f.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(30))
        panel = Image.new("RGBA", region.size, (255, 255, 255, 40))
        region.alpha_composite(panel)
        m = Image.new("L", region.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, region.width - 1, region.height - 1), 50, fill=255)
        k = clamp(t / 0.3)
        f.paste(region, (x0, y0), m.point(lambda v: int(v * k)))
        d = ImageDraw.Draw(f)
        d.rounded_rectangle((x0, y0, x1, y1), 50, outline=(255, 255, 255, int(120 * k)), width=3)
        d.text((x0 + 60, y0 + 50), s.get("label", "").upper(), font=label_font(40), fill=GRAY)
        p = ease_inout((t - 0.4) / 2.2)
        val = a + (b - a) * p
        txt = (f"{val:.0f}" if b >= 10 else f"{val:.1f}") + suf
        d.text((x0 + 60, y0 + 105), txt, font=font(ANTON, 150), fill=WHITE)
        gx0, gy0, gx1, gy1 = x0 + 60, y0 + 330, x1 - 60, y1 - 60
        n = len(pts)
        xy = [(gx0 + (gx1 - gx0) * i / (n - 1), gy1 - (gy1 - gy0) * v) for i, v in enumerate(pts)]
        upto = p * (n - 1)
        shown = [xy[i] for i in range(int(upto) + 1)]
        if int(upto) < n - 1:
            fr = upto - int(upto); a0, a1 = xy[int(upto)], xy[int(upto) + 1]
            shown.append((a0[0] + (a1[0] - a0[0]) * fr, a0[1] + (a1[1] - a0[1]) * fr))
        if len(shown) > 1:
            d.polygon(shown + [(shown[-1][0], gy1), (gx0, gy1)], fill=GREEN + (60,))
            d.line(shown, fill=GREEN, width=10, joint="curve")
            ex, ey = shown[-1]
            d.ellipse((ex - 16, ey - 16, ex + 16, ey + 16), fill=WHITE, outline=GREEN, width=6)
        return f
    return dur, draw


def sc_image(s):
    """A finished post image (e.g. the stats review) held on screen with a gentle zoom, long enough to read."""
    dur = s.get("dur", 4.5)
    src = Image.open(s["image"]).convert("RGBA")
    def draw(t):
        f = background(s.get("theme", "squad"))
        z = 1 + 0.04 * t / dur
        im = src.resize((int(RW * z), int(src.height * RW * z / src.width)), Image.LANCZOS)
        paste_center(f, im, RW / 2, RH / 2, alpha=clamp(t / 0.3))
        return f
    return dur, draw


def sc_swipe(s):
    dur = s.get("dur", 3.6)
    def draw(t):
        f = background(s.get("theme", "comparison"))
        logo_small(f)
        headline(f, s.get("title", "BEFORE vs AFTER"), 230, 100, WHITE, PURPLE, t / 0.4)
        layer_b = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        layer_a = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
        paste_center(layer_b, glow_behind(card_img(s["before"], 1050), GRAY, 20, 100), RW / 2, 1080)
        paste_center(layer_a, glow_behind(card_img(s["after"], 1050), GOLD, 24, 160), RW / 2, 1080)
        p = ease_inout((t - 0.8) / 1.6)
        sx = int(RW * (1 - p))
        f.alpha_composite(layer_b)
        if sx < RW:
            mask = Image.new("L", (RW, RH), 0); ImageDraw.Draw(mask).rectangle((sx, 0, RW, RH), fill=255)
            f.paste(layer_a, (0, 0), Image.composite(layer_a.getchannel("A"), Image.new("L", (RW, RH), 0), mask))
            d = ImageDraw.Draw(f)
            d.line((sx, 520, sx, 1650), fill=WHITE, width=6)
            d.ellipse((sx - 40, 1045, sx + 40, 1125), fill=WHITE)
            d.text((sx, 1085), "< >", font=label_font(30), fill=BLACK, anchor="mm")
        d = ImageDraw.Draw(f)
        d.text((120, 1720), "BEFORE", font=label_font(44), fill=GRAY)
        d.text((RW - 120, 1720), "AFTER", font=label_font(44), fill=GOLD, anchor="ra")
        return f
    return dur, draw


TIER_COL = {"S": (255, 82, 82), "A": (255, 167, 38), "B": (255, 214, 0), "C": (102, 187, 106), "D": (66, 165, 245)}


def sc_tierlist(s):
    tiers = list(s["tiers"].items())[:5]
    items = [(ti, j, c) for ti, (_, cards) in enumerate(tiers) for j, c in enumerate(cards[:4])]
    gap = s.get("gap", 0.45)
    dur = s.get("dur", 0.8 + gap * len(items) + 1.5)
    rows_top, row_h = 430, 260
    def draw(t):
        f = background("top10")
        logo_small(f)
        headline(f, s.get("title", "TIER LIST"), 230, 104, WHITE, PURPLE, t / 0.4)
        d = ImageDraw.Draw(f)
        for i, (name, _) in enumerate(tiers):
            y = rows_top + i * (row_h + 20)
            d.rounded_rectangle((60, y, RW - 60, y + row_h), 26, fill=(18, 18, 24, 255), outline=(60, 60, 70), width=2)
            d.rounded_rectangle((60, y, 220, y + row_h), 26, fill=TIER_COL.get(name, GRAY))
            d.rectangle((190, y, 220, y + row_h), fill=TIER_COL.get(name, GRAY))
            d.text((140, y + row_h / 2), name, font=font(ANTON, 130), fill=BLACK, anchor="mm")
        for k, (ti, j, c) in enumerate(items):
            t0 = 0.8 + k * gap
            if t < t0:
                break
            p = ease_back((t - t0) / 0.4)
            ty = rows_top + ti * (row_h + 20) + row_h / 2
            cx = 340 + j * 200
            sy = ty - 160
            paste_center(f, card_img(c, row_h - 30), cx, sy + (ty - sy) * clamp(p, 0, 1.2), 1.0 + 0.4 * (1 - clamp(p)),
                         alpha=clamp((t - t0) / 0.15))
        return f
    return dur, draw


def sc_outro(s):
    dur = s.get("dur", 2.4)
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255))
    logo = logo.resize((720, int(720 * logo.height / logo.width)), Image.LANCZOS)
    def draw(t):
        f = background("news")
        paste_center(f, glow_behind(logo, RED, 30, 140), RW / 2, 760, 0.8 + 0.2 * ease_back(t / 0.5), alpha=clamp(t / 0.3))
        flipped = t > 1.3
        w, h = 560, 140
        btn = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bd = ImageDraw.Draw(btn)
        if flipped:
            bd.rounded_rectangle((0, 0, w - 1, h - 1), 70, fill=(40, 40, 46), outline=(110, 110, 120), width=3)
            bd.text((w / 2, h / 2), "Following ✓".replace(" ✓", ""), font=label_font(56), fill=WHITE, anchor="mm")
        else:
            bd.rounded_rectangle((0, 0, w - 1, h - 1), 70, fill=(0, 149, 246))
            bd.text((w / 2, h / 2), "Follow", font=label_font(56), fill=WHITE, anchor="mm")
        press = 1 - 0.08 * math.sin(clamp((t - 1.15) / 0.3) * math.pi)
        paste_center(f, btn, RW / 2, 1180, ease_back((t - 0.4) / 0.4) * press)
        # cursor taps the button
        if 0.7 < t < 2.0:
            cx = RW / 2 + 200 - 160 * ease_inout((t - 0.7) / 0.5)
            cy = 1340 - 140 * ease_inout((t - 0.7) / 0.5)
            cur = Image.new("RGBA", (70, 90), (0, 0, 0, 0))
            ImageDraw.Draw(cur).polygon([(5, 5), (5, 75), (24, 58), (38, 86), (50, 80), (36, 52), (62, 52)], fill=WHITE, outline=BLACK)
            f.alpha_composite(cur, (int(cx), int(cy)))
        paste_center(f, text_layer("DAILY FC MOBILE CARDS, CODES & TIPS", label_font(40), GRAY), RW / 2, 1380, alpha=clamp((t - 0.6) / 0.3))
        return f
    return dur, draw


def sc_stopgame(s):
    """Flash cards in a clean loop, with one beat for the named player's card."""
    STEP, dur = 0.18, s.get("dur", 9.0)
    n = int(dur / STEP)
    target = s["target_card"]
    others = [card for card in s["cards"] if card != target]
    seq = [others[i % len(others)] if others else None for i in range(n)]
    seq[n // 2] = target
    def draw(t):
        f = background(s.get("theme", "event"))
        headline(f, "CAN YOU STOP ON", 480, 92, WHITE, BLUE)  # below the ATB box (y 140-400)
        headline(f, s["target"], 600, 120, GOLD, RED)
        i = min(n - 1, int(t / STEP))
        if seq[i] is not None:
            paste_center(f, card_img(seq[i], 880), RW / 2, 1170)
        headline(f, "COMMENT IF YOU GOT HIM", 1680, 60, WHITE, None)
        return f
    return dur, draw


SCENES = {"image": sc_image, "reveal": sc_reveal, "countdown": sc_countdown, "code": sc_code, "stamp": sc_stamp, "messages": sc_messages,
          "stat": sc_stat, "swipe": sc_swipe, "tierlist": sc_tierlist, "outro": sc_outro, "stopgame": sc_stopgame}


# ---------- polish: sparkles, shake, grain, vignette ----------
import random as _rnd
_SPARK = [(_rnd.Random(i).uniform(-1, 1), _rnd.Random(i + 99).uniform(-1, 1), _rnd.Random(i + 7).uniform(0, 6.28),
           _rnd.Random(i + 3).uniform(6, 16)) for i in range(40)]


def sparkles(frame, t, cx, cy, rx, ry, color=GOLD, k=1.0):
    """Twinkling 4-point stars around a point (k = intensity 0..1)."""
    if k <= 0:
        return
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for ux, uy, ph, sz in _SPARK:
        a = (math.sin(t * 7 + ph) * 0.5 + 0.5) ** 3 * k
        if a < 0.05:
            continue
        x, y, s = cx + ux * rx, cy + uy * ry, sz * (0.6 + a)
        col = color + (int(255 * a),)
        d.polygon([(x, y - s * 2), (x + s * .35, y), (x, y + s * 2), (x - s * .35, y)], fill=col)
        d.polygon([(x - s * 2, y), (x, y + s * .35), (x + s * 2, y), (x, y - s * .35)], fill=col)
    frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.6)))


def shake(frame, t, t0, amp=26, dur=0.35):
    """Camera shake after an impact at t0."""
    if not (t0 <= t < t0 + dur):
        return frame
    k = 1 - (t - t0) / dur
    dx, dy = int(math.sin(t * 95) * amp * k), int(math.cos(t * 77) * amp * k)
    out = Image.new("RGBA", frame.size, BLACK + (255,))
    out.paste(frame.resize((int(RW * 1.04), int(RH * 1.04))), (-int(RW * .02) + dx, -int(RH * .02) + dy))
    return out


_VIG = None
_GRAIN = []
def polish(frame, k):
    """Subtle vignette + animated film grain on every frame."""
    global _VIG
    if _VIG is None:
        v = Image.radial_gradient("L").resize((RW, RH)).point(lambda p: int(min(255, p * 1.25)))
        _VIG = Image.merge("RGBA", [Image.new("L", (RW, RH), 0)] * 3 + [v.point(lambda p: int(p * 0.55))])
        for i in range(6):
            g = Image.effect_noise((RW // 2, RH // 2), 40).resize((RW, RH))
            _GRAIN.append(Image.merge("RGBA", [g, g, g, Image.new("L", (RW, RH), 14)]))
    frame.alpha_composite(_VIG)
    frame.alpha_composite(_GRAIN[k % len(_GRAIN)])
    return frame


def whip(a, b, p):
    """Whip-pan transition: A slides out left with motion blur, B slides in, white flash at the cut."""
    e = ease_inout(p)
    out = Image.new("RGBA", (RW, RH), BLACK + (255,))
    blur = int(40 * math.sin(p * math.pi)) + 1
    sa = a.filter(ImageFilter.BoxBlur(blur)) if blur > 2 else a
    sb = b.filter(ImageFilter.BoxBlur(blur)) if blur > 2 else b
    out.paste(sa, (int(-RW * e), 0))
    out.paste(sb, (int(RW * (1 - e)), 0))
    flash = max(0, 1 - abs(p - 0.5) * 5)
    if flash:
        out.alpha_composite(Image.new("RGBA", (RW, RH), (255, 255, 255, int(170 * flash))))
    return out


# ---------- sound design: (time, sound, volume) per scene ----------
def scene_sfx(s, dur):
    n = s["scene"]
    if n == "reveal":
        return [(0, "riser", .6), (0.85, "sparkle", .6), (1.0, "impact", .9)]
    if n == "countdown":
        per, cnt = s.get("per", 1.1), min(10, len(s["players"]))
        ev = [(0, "whoosh", .5)]
        for k in range(cnt):
            t0 = 0.8 + k * per
            ev += [(t0, "flip", .8), (t0 + 0.05, "whoosh", .45)]
        last = 0.8 + per * (cnt - 1)
        return ev + [(last + 0.75, "impact", .95), (last + 0.8, "sparkle", .7)]
    if n == "code":
        ev = [(0.2, "pop", .7)] + [(1.0 + i * 1.4 / len(s["code"]), "type", .7) for i in range(len(s["code"]))]
        return ev + [(2.7, "click", .8), (2.75, "ding", .8), (2.8, "sparkle", .5)]
    if n == "stamp":
        return [(0.85, "whoosh", .6), (1.0, "stamp", 1.0)]
    if n == "messages":
        return [(0.6 + i * s.get("gap", 0.7), "ding" if i == 0 else "pop", .6) for i in range(len(s["lines"][:5]))]
    if n == "stat":
        return [(0.4, "riser", .5), (2.6, "ding", .7)]
    if n == "stopgame":  # a tick on every card change keeps the rhythm
        return [(k * 0.18, "click", .35) for k in range(int(s.get("dur", 9.0) / 0.18))]
    if n == "swipe":
        return [(0.8, "whoosh", .8), (2.3, "impact", .5)]
    if n == "tierlist":
        cnt = sum(len(v[:4]) for v in list(s["tiers"].values())[:5])
        return [(0.8 + k * s.get("gap", 0.45), "pop", .7) for k in range(cnt)]
    if n == "outro":
        return [(0.4, "pop", .7), (1.3, "click", .9), (1.35, "ding", .5)]
    return []


def mix_audio(events, total, path):
    import numpy as np
    from fmm import sfx
    buf = np.zeros(int(sfx.SR * (total + 1)), dtype=np.float32)
    cache = {}
    for t0, name, vol in events:
        x = cache.setdefault(name, sfx.load(name))
        s = int(t0 * sfx.SR)
        e = min(len(buf), s + len(x))
        buf[s:e] += x[:e - s] * vol
    buf = np.tanh(buf * 0.9)  # soft limiter
    sfx.write(path, buf)


# ---------- renderer ----------
TRANS = 0.32  # whip transition length between scenes (seconds)


def render_reel(reel, out_dir=OUT, music=None, stills=None):
    specs = list(reel["scenes"]) + ([{"scene": "outro"}] if reel.get("outro", True) else [])
    scenes = [SCENES[s["scene"]](s) for s in specs]
    out_dir.mkdir(parents=True, exist_ok=True)
    if stills:  # quick check: save a few frames instead of rendering video
        paths, acc = [], 0
        for i, (dur, fn) in enumerate(scenes):
            for fr in stills:
                p = out_dir / f"{reel['id']}_s{i}_{fr:.1f}.png"
                fn(min(dur * fr, dur - 0.01)).convert("RGB").save(p); paths.append(p)
        return paths
    # timeline: scene, whip, scene, whip, ... ; collect sound events on the global clock
    events, clock = [], 0.0
    for i, ((dur, _), spec) in enumerate(zip(scenes, specs)):
        events += [(clock + t0, n, v) for t0, n, v in scene_sfx(spec, dur)]
        clock += dur
        if i < len(scenes) - 1:
            events.append((clock, "whoosh", .7))
            clock += TRANS
    total = clock
    out = out_dir / f"{reel['id']}.mp4"
    if reel.get("cover"):  # MrBeast-style cover image used as the Reel/Short thumbnail
        from fmm import thumb
        c = reel["cover"]
        thumb.cover(c.get("subject"), c["text"], out_dir / f"{reel['id']}_cover.jpg", sub=c.get("sub"),
                    color=c.get("color", "red"), emoji=c.get("emoji", "wow"))
    wav = out_dir / f"{reel['id']}_sfx.wav"
    mix_audio(events, total, wav)
    music, start = music or reel.get("music"), 0
    if not music:  # copyright-safe library track (fmm.music)
        from fmm import music as lib
        music, start = lib.pick()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-",
           "-i", str(wav)]
    if music:  # music under the sound effects
        cmd += ["-stream_loop", "-1", "-ss", str(start), "-i", music, "-filter_complex",
                f"[2:a]volume=0.35,afade=t=out:st={max(0, total - 1):.2f}:d=1[m];"
                "[1:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]", "-map", "0:v", "-map", "[a]"]
    if not music:
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]  # reel-kit loudness target
    cmd += ["-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    k = 0
    def emit(img):
        nonlocal k
        enc.stdin.write(polish(img, k).convert("RGB").tobytes()); k += 1
    for i, (dur, fn) in enumerate(scenes):
        for j in range(int(round(dur * FPS))):
            emit(fn(j / FPS))
        if i < len(scenes) - 1:
            a, b = fn(dur - 1 / FPS), scenes[i + 1][1](0)
            n = int(round(TRANS * FPS))
            for j in range(n):
                emit(whip(a, b, (j + 1) / (n + 1)))
    enc.stdin.close()
    enc.wait()
    wav.unlink(missing_ok=True)
    # owner rule: no Reel without ATB's video — his reaction clip boxed top-right for the whole Reel
    from fmm import atb
    cover = out_dir / f"{reel['id']}_cover.jpg"
    if reel.get("cover") and specs[0]["scene"] != "stopgame":
        lead_with_cover(out, cover)
    atb.box(out, reel["id"], voice=reel.get("voice", "default"))  # ATB's voice in every animated Reel
    if not cover.exists():  # never a black/empty cover: take a full, settled frame
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.6", "-i", str(out), "-frames:v", "1", "-q:v", "2",
                        str(cover)], check=True)
    return out


def progress_bar(mp4, color="0xFFD700", h=10):
    """Thin gold bar along the bottom that fills over the Reel (retention cue used by top Shorts; ffmpeg-only idea
    from open-source shortsmith). Done once per file: a .bar marker stops a retry from adding a second bar."""
    mp4 = Path(mp4)
    mark = mp4.with_name(mp4.name + ".bar")
    if mark.exists():
        return mp4
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                               capture_output=True, text=True).stdout.strip() or 0)
    if dur <= 0:
        return mp4
    tmp = mp4.with_name(mp4.stem + "_bar.mp4")
    # a full-width strip slides in from the left: x = -w + w*t/dur, so it is t/dur full at time t
    fc = (f"color=c={color}:s=1080x{h}:r=30[b];[0:v]scale=1080:1920,setsar=1[v0];"
          f"[v0][b]overlay=x='-w+w*t/{dur:.3f}':y=H-{h}:shortest=1,format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-filter_complex", fc, "-map", "[v]", "-map", "0:a?",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-c:a", "copy", "-movflags", "+faststart",
                    str(tmp)], check=True)
    tmp.replace(mp4)
    mark.touch()
    return mp4


def lead_with_cover(mp4, cover, secs=0.7):
    """Open the Reel on its payoff: the cover (final card / goal / verdict + big text + ATB face) for secs, then
    the Reel. Top Shorts show the result in frame 0; it is also what platforms show when no cover is set."""
    mp4, cover = Path(mp4), Path(cover)
    if not cover.exists():
        return mp4
    tmp = mp4.with_name(mp4.stem + "_lead.mp4")
    has_a = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                            "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip()
    fc = (f"[0:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[c];[1:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[m];"
          + ("[2:a]atrim=0:%s[s];[1:a]aresample=44100[ma];[c][s][m][ma]concat=n=2:v=1:a=1[v][a]" % secs if has_a
             else "[c][m]concat=n=2:v=1:a=0[v]"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(secs), "-i", str(cover), "-i", str(mp4),
                    "-f", "lavfi", "-t", str(secs), "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex", fc,
                    "-map", "[v]", *(["-map", "[a]", "-c:a", "aac", "-b:a", "160k"] if has_a else []),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-movflags", "+faststart", str(tmp)], check=True)
    tmp.replace(mp4)
    return mp4


if __name__ == "__main__":
    args = sys.argv[1:]
    check = "--check" in args
    data = json.loads(Path([a for a in args if not a.startswith("--")][0]).read_text(encoding="utf-8"))
    for reel in data["reels"]:
        print("made", render_reel(reel, stills=[0.35, 0.95] if check else None))
