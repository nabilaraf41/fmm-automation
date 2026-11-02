"""Star Shards prices of Star Signings cards, cross-checked on two sites (owner rule: 2 sources).

    python -m fmm.shards     -> list cards whose price both sites agree on

Sources: fcmobileforum.com ShardIQ (JSON API) and fcmobilesquad.com/star-signings-players (HTML pages).
A price counts only when both list the same card (name + OVR + position) within 5% of each other.
"""
import html, re, unicodedata
import requests

UA = {"User-Agent": "Mozilla/5.0 (compatible; FMM-watcher/1.0; +https://nabilaraf41.github.io/)"}
BUDGET = 14000  # owner: under 14k shards = low budget


def norm(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def forum():
    r = requests.get("https://fcmobileforum.com/api/v1/shardiq/cards", params={"limit": 5000}, headers=UA, timeout=60)
    r.raise_for_status()
    return {(norm(c["player_name"]), c["ovr"], c["position"]): c["shard_value"] for c in r.json()["results"]
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


def prices():
    """{(name, ovr, pos): shards} for cards both sites agree on (within 5%); the forum's number is used."""
    a, b = forum(), squad()
    return {k: v for k, v in a.items() if k in b and abs(v - b[k]) <= 0.05 * max(v, b[k])}


def budget_cards():
    """Cards under BUDGET whose price both sites agree on, as player dicts with a card image (built if needed)."""
    from fmm import fmf, renderz
    r = requests.get("https://fcmobileforum.com/api/v1/shardiq/cards", params={"limit": 5000}, headers=UA, timeout=60)
    r.raise_for_status()
    ok = prices()
    out, seen = [], set()
    for c in sorted(r.json()["results"], key=lambda c: (-c["ovr"], c.get("shard_value") or 0)):
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


if __name__ == "__main__":
    a, b = forum(), squad()
    both = prices()
    print(f"forum {len(a)} cards, fcmobilesquad {len(b)} cards, agreed {len(both)}")
    for k, v in sorted(both.items(), key=lambda x: x[1]):
        print(f"{v:>7,}  {k[1]} {k[2]} {k[0]}", "(low budget)" if v < BUDGET else "")
    for k in sorted(set(a) & set(b) - set(both)):
        print("price mismatch:", k, a[k], b[k])
