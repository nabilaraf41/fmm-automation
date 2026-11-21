"""Thursday "New players: shard cost" (22 Nov upgrade; Fc Messi's version got 367K). After the Thursday drop, once a
week, the week's new cards with their FC Mobile Forum shard price, photo + Reel. Counts as the day's one extra post.
"""
import datetime as dt, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "shardcost"


def build(outdir=OUT):
    from fmm import slots, shards, shardguide
    fresh, _, _ = slots.latest_players()
    week_ago = (dt.datetime.now(dt.UTC) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    ok = shards.prices()
    items, seen = [], set()
    for p in sorted(fresh.values(), key=lambda p: -(p.get("ovr") or 0)):
        price = shards.price_of(p, ok)
        if (p.get("added") or "") < week_ago or not price or p["name"] in seen:
            continue
        p = dict(p); p["card"] = p.get("card") or slots.ensure_card(p, fresh)
        if p["card"]:
            seen.add(p["name"]); items.append(({"short_pros": ["NEW THIS WEEK"]}, p, price))
    if len(items) < 3:
        return None, None
    items = items[:6]
    Path(outdir).mkdir(parents=True, exist_ok=True)
    img = shardguide.slide("NEW PLAYERS COST", (200, 255, 0), items, Path(outdir) / "shardcost.png", None)
    cap = ("New players' shard cost this week 💎👇\n\n" +
           "\n".join(f"{p['ovr']} {p['name']} ({p['pos']}): {price:,} shards" for _, p, price in items) +
           "\n\nWho are you buying? 👇\n\nPrices: FC Mobile Forum.\n\n#FCMobile #FIFAMobile #EAFC #FCMobileShards #FMM")
    return img, cap


def post_due(now):
    """Thursday or Friday 15:00-21:59 BDT, once a week (prices sometimes appear a day after the drop)."""
    from fmm import poster
    if now.weekday() not in (3, 4) or not 15 <= now.hour < 22:
        return None
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    monday = (now - dt.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    if any(e.get("type") == "shardcost" and e.get("at", "") >= monday for e in log):
        return None
    img, cap = build()
    return poster.post("photo", img, cap, "both", "shardcost") if img else None
