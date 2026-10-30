"""Players from fcmobileforum.com (reachable from the cloud, unlike RenderZ).

Reads the newest cards from /players (one page per run), maps them to the same player format as
fmm.renderz, and builds card images from the forum's card background + player render.

    python -m fmm.fmf          -> print newest cards
"""
import io, json, re, urllib.request
from fmm import renderz

URL = "https://fcmobileforum.com/players"
UA = {"User-Agent": "Mozilla/5.0 (compatible; FMM-watcher/1.0; +https://nabilaraf41.github.io/)"}
ATTR = {"acceleration": "acc", "sprintSpeed": "spd", "finishing": "fin", "shotPower": "sho", "longShot": "lsa",
        "positioning": "pos", "volleys": "vol", "headingAccuracy": "hea", "shortPassing": "spa", "longPassing": "lpa",
        "vision": "vis", "crossing": "cro", "curve": "cur", "dribbling": "dri", "agility": "agi", "balance": "bal",
        "reactions": "rea", "ballControl": "bac", "marking": "mrk", "standingTackle": "stt", "slidingTackle": "slt",
        "awareness": "awr", "strength": "str", "jumping": "jmp", "stamina": "sta", "aggression": "agg",
        "gkDiving": "gkd", "gkHandling": "gkh", "gkKicking": "gkk", "gkPositioning": "gkp", "gkReflexes": "ref"}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read()


def flight_text(page):
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', page, flags=re.S)
    return "".join(json.loads('"' + c + '"') for c in chunks)


def initial_players(text):
    i = text.find('"initialPlayers":[')
    if i < 0:
        raise RuntimeError("fcmobileforum layout changed: initialPlayers not found")
    i += len('"initialPlayers":')
    depth, in_str, j = 0, False, i
    while j < len(text):
        c = text[j]
        if in_str:
            if c == "\\": j += 2; continue
            if c == '"': in_str = False
        elif c == '"': in_str = True
        elif c in "[{": depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return json.loads(text[i:j + 1])
        j += 1
    raise RuntimeError("unterminated initialPlayers")


def slim(x):
    r = x.get("_rawCard") or {}
    at = r.get("attributes") or {}
    ps = x.get("playStyles") if isinstance(x.get("playStyles"), list) else []
    return {
        "id": f"f{x.get('uniqueId') or r.get('id')}", "name": x.get("playerName") or r.get("playerName"),
        "full_name": r.get("fullName"), "ovr": int(r.get("rating") or x.get("rating") or 0),
        "pos": r.get("position") or x.get("playerPosition"),
        "program": (r.get("eventName") or "").replace("programname_", "").upper(),
        "weak_foot": r.get("weakFoot"), "skill_moves": r.get("skillMove"),
        "work_rates": [(r.get("workRateAtt") or 0) + 1, (r.get("workRateDef") or 0) + 1],
        "height": r.get("height"), "weight": r.get("weight"), "club": r.get("club"), "nation": r.get("nation"),
        "stats": {ATTR[k]: v for k, v in at.items() if k in ATTR and isinstance(v, (int, float))},
        "playstyles": [str(p.get("name", p)).replace("_", " ").title() if isinstance(p, dict) else str(p) for p in ps],
        "added": r.get("createdAt"), "img_player": r.get("playerImage") or x.get("imageUrl"),
        "img_bg": r.get("cardArtBackgroundUrl"), "layout": {}, "colors": {},
        "url": "https://fcmobileforum.com/players", "source": "fcmobileforum",
    }


def latest():
    players = [slim(x) for x in initial_players(flight_text(fetch(URL).decode("utf-8", "ignore")))]
    return sorted(players, key=lambda p: p.get("added") or "", reverse=True)


def build_card(p, size=1024):
    """Same composition as RenderZ cards (forum bg + render + default 256-grid layout)."""
    renderz_fetch = renderz.fetch
    renderz.fetch = fetch          # use this site's fetcher for the image downloads
    try:
        return renderz.build_card(p, size)
    finally:
        renderz.fetch = renderz_fetch


if __name__ == "__main__":
    for p in latest()[:8]:
        print(p["added"], p["ovr"], p["pos"], p["name"], p["program"], len(p["stats"]), "stats")
