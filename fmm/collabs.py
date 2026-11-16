"""Who to invite as Instagram collaborator on each post (owner, 16 Nov): up to 5 per post, chosen by what each partner
actually ACCEPTS per post type ("reel:statrank", "photo:xi", ...), plus rotating spots so new/quiet partners still get turns.

content/collaborators.json: {"rotate": [...partners, listed twice = extra turns...], "always": [...], "prefer": {...}}
content/collab_stats.json:  {name: {"reel:statrank": [accepted, invited], ...}}  refreshed weekly (refresh()).
"""
import json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "content" / "collaborators.json"
STATS = ROOT / "content" / "collab_stats.json"
MAX = 5          # Instagram shows up to 5 collaborators; poster falls back to 3 if the API refuses 5
ROTATING = 2     # of those, spots that rotate through everyone (fair chances, keeps learning)


def _load(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def score(stats, name, kind):
    """Chance this partner accepts this post type: their rate for the type, pulled toward their overall rate."""
    s = stats.get(name, {})
    acc = sum(a for a, _ in s.values()); inv = sum(i for _, i in s.values())
    overall = (acc + 1) / (inv + 2)            # new partner -> 0.5
    a, i = s.get(kind, [0, 0])
    return (a + 2 * overall) / (i + 2)


def pick(kind, n_post):
    """Names to invite on post #n_post of this kind ("reel:statrank"); [] when none configured."""
    cfg, stats = _load(CFG, {}), _load(STATS, {})
    clean = lambda xs: [x.lstrip("@") for x in xs if x]
    rot = clean(cfg.get("rotate", cfg.get("usernames", [])))
    # "only": {"name": ["photo"]} -> that partner is invited only on those post kinds (aftab.fc asked: posts, not Reels)
    only = cfg.get("only", {})
    ok = lambda n: not only.get(n) or kind.split(":")[0] in only[n] or kind in only[n]
    rot = [n for n in rot if ok(n)]
    people = list(dict.fromkeys(rot + clean(cfg.get("always", []))))
    if not people:
        return []
    names = clean(cfg.get("always", []))
    for name, kinds in cfg.get("prefer", {}).items():   # manual overrides still win
        if kind in kinds and name not in names:
            names.append(name)
    best = sorted((p for p in people if p not in names), key=lambda p: -score(stats, p, kind))
    names += best[:max(0, MAX - ROTATING - len(names))]
    k = (n_post * ROTATING) % len(rot) if rot else 0
    for p in rot[k:] + rot[:k]:                           # rotating spots (names listed twice = more turns)
        if len(names) >= MAX:
            break
        if p not in names:
            names.append(p)
    return names[:MAX]


def refresh(token, log):
    """Weekly: read invite status of every Instagram post since collabs began -> collab_stats.json."""
    import requests
    stats = {}
    for e in log:
        ig = str(e.get("instagram") or "")
        if e.get("at", "") < "2026-11-11" or not ig.isdigit() or "trial" in str(e.get("type")):
            continue
        r = requests.get(f"https://graph.facebook.com/v21.0/{ig}/collaborators",
                         params={"access_token": token}, timeout=30).json()
        kind = f"{e.get('kind')}:{e.get('type') or 'other'}"
        for c in r.get("data", []):
            row = stats.setdefault(c["username"], {}).setdefault(kind, [0, 0])
            row[1] += 1
            row[0] += c.get("invite_status") == "Accepted"
        time.sleep(0.2)
    stats["_updated"] = time.time()  # file dates are useless on the cloud (fresh checkout)
    STATS.write_text(json.dumps(stats, indent=1), encoding="utf-8")
    return stats


def stale(days=6):
    return time.time() - _load(STATS, {}).get("_updated", 0) > days * 86400


if __name__ == "__main__":
    # self-check: the type-specialist ranks first for its type, list never repeats, max 5
    s = {"a": {"photo:xi": [5, 5]}, "b": {"photo:xi": [0, 5]}, "c": {}}
    assert score(s, "a", "photo:xi") > score(s, "c", "photo:xi") > score(s, "b", "photo:xi")
    print("ok")
