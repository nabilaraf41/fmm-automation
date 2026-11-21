"""Weekly "FMM Shard Guide" carousel (owner 16 Nov, leap_fm style): 3 slides = MUST CLAIM / WORTH THE SHARDS /
WORTH BUT WAIT, 6 cards each with shard price + one reason. Verdicts = our review score (fmm.review), prices = FC Mobile
Forum (fmm.shards). Posted Friday 13:00 as an Instagram/Facebook carousel.
"""
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw

from fmm import brand, review as rv, shards

TIERS = [("MUST CLAIM", "MUST BUY", (40, 200, 90)), ("WORTH THE SHARDS", "WORTH IT", (255, 200, 0)),
         ("WORTH BUT WAIT", "SITUATIONAL", (255, 140, 40))]


def pick(pool, fresh_ids=()):
    """{tier verdict: [(review, player, price)]} best score first, newest cards first on ties, 6 per tier."""
    forum = shards.forum_cards()
    ok = shards.prices(forum)
    art = {(shards.norm(c["player_name"]), c["ovr"], c["position"]): (c.get("card") or {}, c) for c in forum}
    idx = {(shards.norm(p["name"]), p["ovr"], p["pos"]): p for p in pool if p.get("name")}
    out, seen = {}, set()
    rows = []
    for k, price in ok.items():
        p = idx.get(k)
        if not p or p["name"] in seen:
            continue
        r = rv.review(p, pool)
        a, fc = art.get(k, ({}, {}))
        p = {**p, "img_player": p.get("img_player") or a.get("playerImage") or fc.get("player_card"),
             "img_bg": p.get("img_bg") or a.get("cardArtBackgroundUrl"), "forum_id": fc.get("id")}
        rows.append((r, p, price))
    rows.sort(key=lambda t: (-t[0]["score"], str(t[1]["id"]) not in fresh_ids, t[2]))
    for r, p, price in rows:
        if p["name"] in seen or len(out.setdefault(r["verdict"], [])) >= 6:
            continue
        seen.add(p["name"])
        out[r["verdict"]].append((r, p, price))
    return out


def slide(title, color, items, out, n):
    img, d, _ = brand.base("event", None, (1080, 1350))
    img = img.convert("RGBA"); d = ImageDraw.Draw(img)
    d.text((540, 95), "FMM SHARD GUIDE", font=brand.label_font(34), fill=(255, 255, 255), anchor="mm")
    tw = d.textlength(title, font=brand.font("Anton-Regular.ttf", 92))
    d.rounded_rectangle((540 - tw / 2 - 40, 130, 540 + tw / 2 + 40, 250), 30, fill=color + (255,))
    d.text((540, 190), title, font=brand.font("Anton-Regular.ttf", 92), fill=(10, 10, 10), anchor="mm")
    for i, (r, p, price) in enumerate(items):
        cx, cy = 190 + (i % 3) * 350, 300 + (i // 3) * 500
        card = brand.fit_card(str(p["card"]), 230, 300)
        img.alpha_composite(card, (int(cx - card.width / 2), cy))
        d.text((cx, cy + 320), f"{price:,} SHARDS", font=brand.font("Anton-Regular.ttf", 40), fill=(255, 215, 0), anchor="mm")
        why = (r.get("short_pros") or [r.get("verdict", "")])[0]
        for j, ln in enumerate(textwrap.wrap(f"{p['pos']}: {why}", 24)[:3]):
            d.text((cx, cy + 365 + j * 34), ln.upper(), font=brand.label_font(24), fill=(255, 255, 255), anchor="mm")
    d.text((540, 1300), (f"{n}/3  •  " if n else "") + "PRICES: FC MOBILE FORUM", font=brand.label_font(24), fill=(200, 200, 200), anchor="mm")
    img.convert("RGB").save(out, quality=94)
    return out


def build(pool, fresh, outdir, ensure_card):
    picked = pick(pool, set(map(str, fresh)))
    files, lines = [], []
    for n, (title, verdict, color) in enumerate(TIERS, 1):
        items = []
        for r, p, price in picked.get(verdict, []):
            p = dict(p)
            try:
                p["card"] = ensure_card(p, fresh)
            except Exception:
                p["card"] = None
            if not p.get("card") and p.get("img_bg"):  # build from FC Mobile Forum's card art (like Budget XI)
                from fmm import fmf, renderz
                path = renderz.CARDS / f"s{p.get('forum_id') or p['id']}.png"
                if not path.exists():
                    try:
                        fmf.build_card({**p, "layout": {}, "colors": {}}).save(path)
                    except Exception:
                        path = None
                p["card"] = str(path) if path and Path(path).exists() else None
            if p.get("card"):
                items.append((r, p, price))
        if not items:
            continue
        files.append(slide(title, color, items, Path(outdir) / f"guide_{n}.png", n))
        lines.append(f"{title}: " + ", ".join(f"{p['ovr']} {p['name']} ({price:,})" for _, p, price in items))
    caption = ("FMM Shard Guide: what to spend your Star Shards on this week 💎🔥\n\n" + "\n\n".join(lines) +
               "\n\nSwipe for all 3 lists 👉 Save this before you spend 📌\n\nPrices: FC Mobile Forum.\n\n"
               "#FCMobile #FIFAMobile #EAFC #FCMobileShards #FMM")
    return files, caption
