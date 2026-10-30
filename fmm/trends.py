"""What's trending in FC Mobile on YouTube right now (official YouTube Data API search).

Looks at the most-viewed FC Mobile videos from the last 24h in the target regions and pulls out
topic signals: player names, events, and content types (codes, pack opening, draft, tier list...).
Only titles/tags are read as signals; nothing is copied.

    python -m fmm.trends            -> prints and saves content/trends.json
"""
import collections, datetime as dt, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "trends.json"
REGIONS = ["US", "GB", "IN"]  # high-pay + reach (search.list costs 100 quota units each; 10,000/day free)
TOPICS = {"code": r"\bcodes?\b|redeem", "pack": r"pack opening|packs?\b", "draft": r"\bdraft",
          "tierlist": r"tier ?list", "top": r"\btop ?\d+|best ", "review": r"review|worth it|is he",
          "event": r"event|toty|tots|icons?|heroes|ballon|halloween|scream|ucl|anniversary",
          "f2p": r"f2p|free to play|free", "tactics": r"formation|tactic|skill|tutorial|how to",
          "upgrade": r"rank ?up|training|upgrade"}


def run():
    from fmm import youtube
    yt = youtube.service()
    since = (dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    titles = []
    for region in REGIONS:
        res = yt.search().list(part="snippet", q="FC Mobile", type="video", order="viewCount", maxResults=25,
                               publishedAfter=since, regionCode=region, relevanceLanguage="en").execute()
        titles += [i["snippet"]["title"] for i in res.get("items", [])]
    text = " ".join(titles).lower()
    topics = collections.Counter({k: len(re.findall(v, text)) for k, v in TOPICS.items()})
    db = json.loads((ROOT / "content" / "players_db.json").read_text(encoding="utf-8"))["players"] \
        if (ROOT / "content" / "players_db.json").exists() else {}
    names = collections.Counter()
    for p in db.values():
        n = (p.get("name") or "").lower()
        if len(n) >= 4 and n in text:
            names[p["name"]] = text.count(n)
    out = {"at": dt.datetime.now(dt.UTC).replace(tzinfo=None).isoformat(timespec="minutes") + "Z",
           "topics": topics.most_common(), "players": names.most_common(10), "sample_titles": titles[:12]}
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def load():
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except Exception:
        return {"topics": [], "players": []}


if __name__ == "__main__":
    t = run()
    print("topics:", t["topics"][:6])
    print("players:", t["players"])
    print("titles:", *t["sample_titles"][:6], sep="\n  ")
