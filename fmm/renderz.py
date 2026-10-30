"""New-player watcher for renderz.app (FC Mobile database).

Reads the "latest players" list (one page, light use), keeps a local player DB with stats, and builds
each new card image from RenderZ's background + player render, laid out like the in-game card.

    python -m fmm.renderz            -> fetch, print new players, save cards to assets/cards/rz/
    python -m fmm.renderz --seed     -> first run: store current players without treating them as "new"
"""
import io, json, re, sys, time, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "content" / "players_db.json"
CARDS = ROOT / "assets" / "cards" / "rz"
LIST_URL = "https://renderz.app/players?sortType=added&sortDirection=DESC"
UA = {"User-Agent": "Mozilla/5.0 (compatible; FMM-watcher/1.0; +https://nabilaraf41.github.io/)"}

STAT_NAMES = {"acc": "Acceleration", "spd": "Sprint Speed", "fin": "Finishing", "sho": "Shot Power", "lsa": "Long Shots",
              "pos": "Positioning", "vol": "Volleys", "hea": "Heading", "spa": "Short Passing", "lpa": "Long Passing",
              "vis": "Vision", "cro": "Crossing", "cur": "Curve", "dri": "Dribbling", "agi": "Agility", "bal": "Balance",
              "rea": "Reactions", "bac": "Ball Control", "mrk": "Marking", "stt": "Standing Tackle", "slt": "Sliding Tackle",
              "awr": "Defensive Awareness", "str": "Strength", "jmp": "Jumping", "sta": "Stamina", "agg": "Aggression",
              "gkd": "GK Diving", "gkh": "GK Handling", "gkk": "GK Kicking", "gkp": "GK Positioning", "ref": "GK Reflexes"}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return r.read()


def js_to_json(src):
    """Quote bare object keys outside strings so a JS object literal parses as JSON."""
    out, i, n, in_str = [], 0, len(src), False
    while i < n:
        c = src[i]
        if in_str:
            out.append(c)
            if c == "\\":
                out.append(src[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if (c.isalpha() or c in "_$") and out and out[-1] in "{,":
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_$"):
                j += 1
            if j < n and src[j] == ":":
                out.append(f'"{src[i:j]}"'); i = j; continue
        out.append(c); i += 1
    s = "".join(out)
    return re.sub(r"(?<=[:\[,])\s*(?:void 0|undefined)\s*(?=[,}\]])", "null", s)


def extract_array(page, key="players:["):
    i = page.find(key)
    if i < 0:
        raise RuntimeError("RenderZ layout changed: players list not found")
    i += len(key) - 1
    depth, in_str, j = 0, False, i
    while j < len(page):
        c = page[j]
        if in_str:
            if c == "\\": j += 2; continue
            if c == '"': in_str = False
        elif c == '"': in_str = True
        elif c in "[{": depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return json.loads(js_to_json(page[i:j + 1]))
        j += 1
    raise RuntimeError("unterminated players array")


def stars(n):
    try:
        n = int(re.search(r"\d", str(n)).group())
    except Exception:
        return ""
    return "★" * n + "☆" * (5 - n)


def slim(p):
    """Keep what FMM needs (facts only)."""
    st = p.get("stats") or {}
    return {
        "id": p.get("assetId") or p.get("id"), "name": p.get("cardName") or p.get("lastName"),
        "full_name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip(),
        "ovr": p.get("rating"), "pos": p.get("position"), "program": p.get("source"),
        "weak_foot": p.get("weakFoot"), "skill_moves": p.get("skillMovesLevel"),
        "work_rates": [p.get("workRateAtt"), p.get("workRateDef")], "height": p.get("height"), "weight": p.get("weight"),
        "stats": {k: v for k, v in st.items() if isinstance(v, (int, float))},
        "avg": p.get("avgStats"), "playstyles": [ps.get("name", "").replace("PLAYSTYLE_", "").replace("_", " ").title()
                                                 for ps in p.get("playStyles") or []],
        "meta": (p.get("metaData") or {}).get("metaRating"), "added": p.get("added"),
        "img_player": (p.get("images") or {}).get("playerCardImage"),
        "img_bg": (p.get("images") or {}).get("playerCardBackground"),
        "layout": ((p.get("animation") or {}).get("layout")) or {},
        "colors": ((p.get("animation") or {}).get("colors")) or {},
        "url": f"https://renderz.app/player/{p.get('assetId') or p.get('id')}",
    }


def build_card(pl, size=1024):
    """Compose bg + player render + OVR/position/name using the card's own layout (256-unit grid)."""
    from fmm.brand import font, title_font
    k = size / 256
    bg = Image.open(io.BytesIO(fetch(pl["img_bg"]))).convert("RGBA").resize((size, size), Image.LANCZOS)
    if pl.get("img_player"):
        ply = Image.open(io.BytesIO(fetch(pl["img_player"]))).convert("RGBA").resize((size, size), Image.LANCZOS)
        bg.alpha_composite(ply)
    d = ImageDraw.Draw(bg)
    L, C = pl.get("layout") or {}, pl.get("colors") or {}
    def col(key):
        h = (C.get(key) or "#FFFFFF").lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    r = L.get("rating") or {"posX": 36, "posY": 4, "sizeX": 80, "fontSize": 36}
    d.text(((r["posX"] + r.get("sizeX", 80) / 2) * k, (r["posY"] + 12) * k), str(pl["ovr"]),
           font=font("Anton-Regular.ttf", int(r.get("fontSize", 36) * k * 1.15)), fill=col("rating"), anchor="ma")
    p = L.get("position") or {"posX": 56, "posY": 64, "fontSize": 24}
    d.text(((p["posX"] + p.get("sizeX", 40) / 2) * k, (p["posY"] + 2) * k), pl["pos"],
           font=title_font(int(p.get("fontSize", 24) * k * 0.8)), fill=col("position"), anchor="ma")
    nm = L.get("name") or {"posX": 128, "posY": 178, "fontSize": 22}
    d.text((nm["posX"] * k, nm["posY"] * k), (pl["name"] or "").upper(),
           font=title_font(int(nm.get("fontSize", 22) * k * 0.85)), fill=col("name"), anchor="mm")
    return bg.crop(bg.getbbox())


def run(seed=False, max_new=12):
    page = fetch(LIST_URL).decode("utf-8", "ignore")
    players = [slim(p) for p in extract_array(page)]
    db = json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else {"players": {}}
    new = [p for p in players if str(p["id"]) not in db["players"]]
    CARDS.mkdir(parents=True, exist_ok=True)
    made = []
    for p in (new if not seed else []) [:max_new]:
        try:
            path = CARDS / f"{p['id']}.png"
            build_card(p).save(path)
            p["card"] = str(path.relative_to(ROOT)).replace("\\", "/")
            made.append(p)
            time.sleep(1.5)  # be gentle
        except Exception as ex:
            print("card failed", p["name"], str(ex)[:120])
    for p in players:
        db["players"].setdefault(str(p["id"]), {k: v for k, v in p.items() if not k.startswith("img_")})
    for p in made:
        db["players"][str(p["id"])].update(card=p["card"], new_since=time.strftime("%Y-%m-%d"))
    DB.parent.mkdir(parents=True, exist_ok=True)
    DB.write_text(json.dumps(db, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"list: {len(players)} | new: {len(new)} | cards made: {len(made)}")
    for p in made:
        print(f"  NEW {p['ovr']} {p['pos']} {p['name']} ({p['program']})")
    return made


if __name__ == "__main__":
    run(seed="--seed" in sys.argv)
