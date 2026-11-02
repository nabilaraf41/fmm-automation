"""Star Shards prices of Star Signings cards, cross-checked on two sites (owner rule: 2 sources).

    python -m fmm.shards        -> list cards whose price both sites agree on
    python -m fmm.shards save   -> (PC) save the forum's prices for the cloud

Sources: fcmobileforum.com ShardIQ (JSON API) and fcmobilesquad.com/star-signings-players (HTML pages).
A price counts only when both list the same card (name + OVR + position) within 5% of each other.
The forum refuses cloud servers (403), so the cloud uses the copy the PC saved (at most MAX_AGE_DAYS old).
"""
import datetime as dt, html, json, re, unicodedata
from pathlib import Path
import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; FMM-watcher/1.0; +https://nabilaraf41.github.io/)"}
BUDGET = 14000  # owner: under 14k shards = low budget
CACHE = Path(__file__).resolve().parent.parent / "content" / "shard_prices.json"
MAX_AGE_DAYS = 3


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def forum_cards():
    """ShardIQ cards: live when reachable, else the PC's saved copy if fresh enough."""
    try:
        r = requests.get("https://fcmobileforum.com/api/v1/shardiq/cards", params={"limit": 5000}, headers=UA, timeout=60)
        r.raise_for_status()
        return r.json()["results"]
    except Exception as ex:
        c = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        if c and dt.datetime.now(dt.UTC) - dt.datetime.fromisoformat(c["saved"]) <= dt.timedelta(days=MAX_AGE_DAYS):
            print(f"forum live prices unavailable ({str(ex)[:40]}), using PC copy from {c['saved'][:16]}")
            return c["cards"]
        raise


def forum():
    return {(norm(c["player_name"]), c["ovr"], c["position"]): c["shard_value"] for c in forum_cards()
            if c.get("shard_value")}


def squad(max_pages=80):
    out = {}
    for page in range(1, max_pages + 1):
        s = requests.get("https://fcmobilesquad.com/star-signings-players", params={"sort": "cheapest", "page": page},
                         headers=UA, timeout=30).text
        cards = []
        for row in s.split("<tr>")[1:]:  # one card per table row, so fields never mix between cards
            m = re.search(r'star-shard-player-name">([^<]+)<.*?mobile-ovr"><strong>(\d+)<.*?mobile-position">([A-Z]+)<'
                          r'.*?mobile-cost">\s*<strong>([\d,]+)<', row, re.S)
            if m:
                n, o, p, c = m.groups()
                cards.append((o, p, n, c))
        new = {(norm(html.unescape(n)), int(o), p): int(c.replace(",", "")) for o, p, n, c in cards}
        if not new or set(new) <= set(out):  # past the last page
            break
        out.update(new)
    return out


def prices(cards=None):
    """{(name, ovr, pos): shards} for cards both sites agree on (within 5%); the forum's number is used."""
    a = {(norm(c["player_name"]), c["ovr"], c["position"]): c["shard_value"] for c in (cards or forum_cards())
         if c.get("shard_value")}
    b = squad()
    return {k: v for k, v in a.items() if k in b and abs(v - b[k]) <= 0.05 * max(v, b[k])}


def budget_cards():
    """Cards under BUDGET whose price both sites agree on, as player dicts with a card image (built if needed)."""
    from fmm import fmf, renderz
    cards = forum_cards()
    ok = prices(cards)
    out, seen = [], set()
    for c in sorted(cards, key=lambda c: (-c["ovr"], c.get("shard_value") or 0)):
        k = (norm(c["player_name"]), c["ovr"], c["position"])
        if k not in ok or ok[k] >= BUDGET or k[0] in seen:
            continue
        art = c.get("card") or {}
        p = {"id": f"s{c['id']}", "name": c["player_name"], "ovr": c["ovr"], "pos": c["position"], "shards": ok[k],
             "img_player": art.get("playerImage") or c.get("player_card"), "img_bg": art.get("cardArtBackgroundUrl"),
             "layout": {}, "colors": {}}
        path = renderz.CARDS / f"{p['id']}.png"
        try:
            if not path.exists():
                renderz.CARDS.mkdir(parents=True, exist_ok=True)
                fmf.build_card(p).save(path)
            p["card"] = str(path)
        except Exception as ex:
            print("card image skipped", p["name"], str(ex)[:60])
            continue
        seen.add(k[0])
        out.append(p)
    return out


def price_of(p, table):
    return table.get((norm(p.get("name")), p.get("ovr"), p.get("pos")))


def save():
    """PC only: keep a copy of the forum's prices for the cloud (only the fields we use)."""
    keep = ("id", "player_name", "ovr", "position", "shard_value", "player_card")
    cards = [{**{k: c.get(k) for k in keep},
              "card": {k: (c.get("card") or {}).get(k) for k in ("playerImage", "cardArtBackgroundUrl")}}
             for c in forum_cards() if c.get("shard_value")]
    CACHE.write_text(json.dumps({"saved": dt.datetime.now(dt.UTC).isoformat(timespec="minutes"), "cards": cards},
                                ensure_ascii=False), encoding="utf-8")
    print(f"saved {len(cards)} forum prices -> {CACHE.name}")


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["save"]:
        save(); sys.exit()
    a, b = forum(), squad()
    both = prices()
    print(f"forum {len(a)} cards, fcmobilesquad {len(b)} cards, agreed {len(both)}")
    for k, v in sorted(both.items(), key=lambda x: x[1]):
        print(f"{v:>7,}  {k[1]} {k[2]} {k[0]}", "(low budget)" if v < BUDGET else "")
    for k in sorted(set(a) & set(b) - set(both)):
        print("price mismatch:", k, a[k], b[k])
