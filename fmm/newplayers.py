"""New-player drop alert (extra posts, outside the 4 daily slots).

When a batch of new cards appears (usually Thursday 07:00 BDT), posts right away:
  1. an announcement Reel  -> countdown of the best new cards, MrBeast-style cover
  2. a "NEW PLAYERS" grid photo -> up to 10 new cards
  3. FMM reviews of the top 3 new cards (photo posts)
Every other new card stays queued for the slots (reviews when no clip of yours is waiting).

    python -m fmm.newplayers           -> check + post
    python -m fmm.newplayers --dry     -> just show what's new
"""
import datetime as dt, json, shutil, sys
from pathlib import Path

from fmm import renderz, slots, review as rv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "newplayers"


def new_batch():
    """Cards on the forum that the DB has never seen (from RenderZ when reachable, else the forum)."""
    from fmm import fmf
    db = json.loads(renderz.DB.read_text(encoding="utf-8"))["players"] if renderz.DB.exists() else {}
    seen = {f"{p.get('name')}|{p.get('ovr')}|{p.get('pos')}" for p in db.values()} | set(db)
    fresh = fmf.latest()
    cutoff = (dt.datetime.now(dt.UTC) - dt.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S")
    new, keys = [], set()
    for p in fresh:  # the forum lists some cards twice: keep one per name|ovr|pos, and only recent releases
        k = f"{p['name']}|{p['ovr']}|{p['pos']}"
        if p["id"] in seen or k in seen or k in keys or (p.get("added") or "") < cutoff:
            continue
        keys.add(k); new.append(p)
    return new, fresh, db


def run(dry=False):
    from fmm import brand, motion, poster
    new, fresh, db = new_batch()
    ok = slots.confirmed_only({p["id"]: p for p in new})  # cross-check before announcing anything
    held = [p for p in new if p["id"] not in ok]
    new = [p for p in new if p["id"] in ok]
    print(f"new cards: {len(new)} confirmed, {len(held)} waiting for confirmation",
          [f"{p['ovr']} {p['name']}" for p in new[:10]])
    if dry or not new:
        return
    held_ids = {p["id"] for p in held}
    for p in fresh:  # unconfirmed cards stay "unseen" so they're announced once confirmed
        if p["id"] not in held_ids:
            db.setdefault(p["id"], {k: v for k, v in p.items() if not k.startswith("img_")})
    renderz.DB.write_text(json.dumps({"players": db}, ensure_ascii=False, indent=0), encoding="utf-8")
    if len(new) < 3:  # a couple of stray cards: let the slots review them, no announcement
        return
    freshmap = {p["id"]: p for p in fresh}
    top = sorted(new, key=lambda p: p.get("ovr") or 0, reverse=True)
    for p in top[:10]:
        p["card"] = slots.ensure_card(p, freshmap)
    top = [p for p in top if p.get("card")]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    program = (top[0].get("program") or "NEW").replace("_", " ")
    names = "\n".join(f"{i + 1}. {p['ovr']} {p['pos']} {p['name']}" for i, p in enumerate(top[:10]))
    tags = "#FCMobile #FCMobile26 #EASportsFCMobile #NewPlayers #FCMobileCards #FMM"
    # 1) announcement Reel
    reel = {"id": "a_drop_reel",
            "cover": {"subject": top[0]["card"], "text": "NEW PLAYERS\nARE HERE!!", "sub": f"UP TO {top[0]['ovr']} OVR",
                      "color": "gold"},
            "scenes": [{"scene": "countdown", "position": "NEW CARDS",
                        "players": [{"name": p["name"], "card": p["card"]} for p in top[:7]][::-1]}]}
    motion.render_reel(reel, OUT)
    (OUT / "a_drop_reel.txt").write_text(
        f"🚨 NEW FC MOBILE PLAYERS JUST DROPPED ({program})\n\n{names}\n\nWho are you going for? 👇\n\n{tags}",
        encoding="utf-8")
    # 2) grid photo
    grid = {"id": "b_drop_grid", "type": "top10", "position": "NEW", "title": "PLAYERS",
            "players": [{"name": p["name"], "card": p["card"], "ovr": p["ovr"]} for p in top[:10]]}
    brand.render(grid, OUT)
    (OUT / "b_drop_grid.txt").write_text(
        f"📋 Every new card in this drop, ranked by OVR:\n\n{names}\n\nSave this for later 📌\n\n{tags}", encoding="utf-8")
    # 3) reviews of the top 3
    pool = list(db.values())
    st = slots.load_state()
    for i, p in enumerate(top[:3]):
        r = rv.review(p, pool)
        post = {"id": f"c_review_{i}", "type": "review", "tag": "New Card Review", "player": p["name"],
                "subtitle": f"{p['ovr']} OVR • {p['pos']}", "card": p["card"], "tier": "gold",
                "pros": r["pros"], "cons": r["cons"], "score": r["score"]}
        brand.render(post, OUT)
        (OUT / f"c_review_{i}.txt").write_text(r["caption"], encoding="utf-8")
        st["featured"] += [str(p["id"]), f"{p['name']}|{p['ovr']}|{p['pos']}"]
    slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    poster.run_queue(OUT, "both", gap=300)  # 5 min apart, never a burst


if __name__ == "__main__":
    run(dry="--dry" in sys.argv)
