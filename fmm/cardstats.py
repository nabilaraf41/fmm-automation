"""Every 120+ OVR card with its six face stats, from FC Mobile Forum's player filter (feeds the Top 10 by stat series).

    python -m fmm.cardstats save   -> (PC) save the list for the cloud (the forum refuses cloud servers, 403)
"""
import datetime as dt, json, sys
from pathlib import Path
import requests

from fmm.fmf import ATTR
from fmm.shards import UA

CACHE = Path(__file__).resolve().parent.parent / "content" / "card_stats.json"
FACE = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]  # stats1..stats6, the order the forum shows them


def fetch(min_ovr=120):
    out, off = [], 0
    while True:
        j = requests.get("https://fcmobileforum.com/api/v1/player-filter",
                         params={"minOvr": min_ovr, "limit": 60, "offset": off}, headers=UA, timeout=60).json()
        for p in j["players"]:
            out.append({"id": f"f{p['id']}", "name": p["playerName"], "ovr": p["ovr"], "pos": p["position"],
                        "program": (p.get("eventName") or "").replace("programname_", "").upper(),
                        "face": {k: p.get(f"stats{i + 1}") or 0 for i, k in enumerate(FACE)},
                        "stats": {ATTR[k]: v for k, v in (p.get("attributes") or {}).items() if k in ATTR},
                        "img_player": p.get("playerImage"), "img_bg": p.get("cardArtBackgroundUrl")})
        off += 60
        if off >= j["total"] or not j["players"]:
            return out


def load(max_age_days=8):
    try:
        return fetch()
    except Exception:
        c = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
        if c and dt.datetime.now(dt.UTC) - dt.datetime.fromisoformat(c["saved"]) <= dt.timedelta(days=max_age_days):
            return c["cards"]
        raise


if __name__ == "__main__":
    if sys.argv[1:] == ["save"]:
        cards = fetch()
        assert cards and all(set(c["face"]) == set(FACE) for c in cards)
        CACHE.write_text(json.dumps({"saved": dt.datetime.now(dt.UTC).isoformat(timespec="minutes"), "cards": cards},
                                    ensure_ascii=False), encoding="utf-8")
        print(f"saved {len(cards)} cards -> {CACHE.name}")
