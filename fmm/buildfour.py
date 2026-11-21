"""'BUILD YOUR BACK FOUR' (owner 21 Nov, menacesoccerhq style): LB/CB/CB/RB columns x 3 price rows (star / mid / budget)
of FC Mobile cards with their shard price; caption gives a shard budget, people comment their 4. Prices: FC Mobile Forum."""
import random, datetime as dt
from pathlib import Path
from PIL import Image, ImageDraw

from fmm import brand, shards
from fmm.attacks import card_for

COLS = [("LB", (225, 60, 70)), ("CB", (150, 80, 230)), ("CB", (40, 140, 255)), ("RB", (245, 160, 30))]
BANDS = [(40000, 10**9), (10000, 30000), (0, 10000)]  # star / mid / budget shard prices


def pick(week):
    cards = shards.forum_cards(); ok = shards.prices(cards)
    rng = random.Random(week)
    used, grid = set(), [[None] * 4 for _ in BANDS]
    for r, (lo, hi) in enumerate(BANDS):
        for c, (pos, _) in enumerate(COLS):
            cands = sorted({(x["player_name"], x["ovr"]): ok[k] for x in cards
                            if x["position"] == pos and x["ovr"] >= 118 and (k := (shards.norm(x["player_name"]), x["ovr"], pos)) in ok
                            and lo <= ok[k] < hi and x["player_name"] not in used}.items(), key=lambda t: -t[0][1])[:8]
            rng.shuffle(cands)
            for (name, ovr), price in cands:
                p = card_for(name, [x for x in cards if x["ovr"] == ovr and x["position"] == pos])
                if p:
                    p["shards"] = price; used.add(name); grid[r][c] = p
                    break
    return grid


def render(grid, budget, out):
    W, H = 1080, 1350
    img, d, _ = brand.base("event", None, (W, H))
    img = img.convert("RGBA"); d = ImageDraw.Draw(img)
    f = brand.font("Anton-Regular.ttf", 96)
    a, b = "BUILD YOUR ", "BACK FOUR"
    wa, wb = d.textlength(a, font=f), d.textlength(b, font=f)
    x = (W - wa - wb) / 2
    d.text((x, 215), a, font=f, fill=(255, 255, 255), anchor="lm"); d.text((x + wa, 215), b, font=f, fill=(200, 255, 0), anchor="lm")
    d.text((W / 2, 300), f"BUDGET: {budget:,} SHARDS", font=brand.label_font(34), fill=(255, 215, 0), anchor="mm")
    for c, (pos, col) in enumerate(COLS):
        cx = 150 + c * 260
        d.text((cx, 360), pos, font=brand.font("Anton-Regular.ttf", 54), fill=(255, 255, 255), anchor="mm")
        d.rectangle((cx - 40, 392, cx + 40, 398), fill=col)
        for r, row in enumerate(grid):
            p = row[c]
            if not p:
                continue
            y = 420 + r * 300
            card = brand.fit_card(p["card"], 220, 240)
            img.alpha_composite(card, (int(cx - card.width / 2), y))
            pill = f"{p['shards']:,}"
            fw = d.textlength(pill, font=brand.font("Anton-Regular.ttf", 40))
            d.rounded_rectangle((cx - fw / 2 - 16, y + 238, cx + fw / 2 + 16, y + 288), 14, fill=(10, 10, 10, 230), outline=col, width=3)
            d.text((cx, y + 263), pill, font=brand.font("Anton-Regular.ttf", 40), fill=(200, 255, 0), anchor="mm")
    d.text((W / 2, H - 30), "PRICES IN STAR SHARDS  •  FC MOBILE FORUM", font=brand.label_font(22), fill=(200, 200, 200), anchor="mm")
    img.convert("RGB").save(out, quality=94)
    return out


def build(outdir, week=None):
    w = week or dt.date.today().isocalendar()[1]
    grid = pick(w)
    if sum(1 for row in grid for p in row if p) < 10:
        return None, None
    top = sum(p["shards"] for p in grid[0] if p)
    budget = int(round(top * 0.55 / 5000) * 5000)
    out = render(grid, budget, Path(outdir) / "backfour.png")
    names = lambda r: ", ".join(f"{p['ovr']} {p['name']} ({p['shards']:,})" for p in grid[r] if p)
    cap = (f"You have {budget:,} Star Shards to build your back four 💎🧱\n\n"
           "Pick one LB, two CBs and one RB without going over the budget. Comment your 4 👇\n\n"
           f"Stars: {names(0)}\nMid: {names(1)}\nBudget: {names(2)}\n\n"
           "Prices: FC Mobile Forum.\n\n#FCMobile #FIFAMobile #EAFC #FCMobileShards #FMM")
    return out, cap
