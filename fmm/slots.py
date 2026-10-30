"""The 4 daily FMM posting slots (Bangladesh time).

    python -m fmm.slots build <slot>   -> 30 min before: check RenderZ, pick + render content into output/slot/
    python -m fmm.slots post           -> at slot time: publish output/slot/ to FB + IG (+ YouTube for Reels)

Slots: 0700 (USA, Reel) · 1300 (EU/India, photo) · 2100 (BD/India, Reel) · 0030 (UK/EU, photo)
New cards are featured first (newest/highest OVR); with nothing new, slots fall back to card battles,
tier lists and countdowns built from the latest cards.
"""
import datetime as dt, json, shutil, sys
from pathlib import Path

from fmm import renderz, review as rv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "slot"
STATE = ROOT / "content" / "featured.json"
SLOTS = {"0700": "reel", "1300": "photo", "2100": "reel", "0030": "photo"}
VERDICT_COLOR = {"MUST BUY": (0, 200, 83), "WORTH IT": (255, 215, 0), "SITUATIONAL": (255, 152, 0), "SKIP": (225, 6, 44)}


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"featured": [], "history": []}


def latest_players():
    """Fresh list from RenderZ when reachable; otherwise (cloud is blocked by RenderZ) the cards
    your PC already collected into the repo: players_db.json + assets/cards/rz/*.png."""
    made = []
    try:
        made = renderz.run()
        page = renderz.fetch(renderz.LIST_URL).decode("utf-8", "ignore")
        fresh = {str(p["id"]): p for p in (renderz.slim(x) for x in renderz.extract_array(page))}
    except Exception as ex:
        print("RenderZ not reachable here:", str(ex)[:80])
        fresh = None
    db = json.loads(renderz.DB.read_text(encoding="utf-8"))["players"] if renderz.DB.exists() else {}
    if fresh is None:  # cloud: fcmobileforum.com allows it
        try:
            from fmm import fmf
            fresh = {p["id"]: p for p in fmf.latest()[:24]}
            for pid, p in fresh.items():
                db.setdefault(pid, {k: v for k, v in p.items() if not k.startswith("img_")})
            renderz.DB.write_text(json.dumps({"players": db}, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"fcmobileforum: {len(fresh)} latest cards")
        except Exception as ex:
            print("fcmobileforum not reachable, using collected cards:", str(ex)[:80])
    if fresh is None:
        recent = sorted(db.values(), key=lambda p: p.get("added") or "", reverse=True)
        fresh = {str(p["id"]): p for p in recent if (renderz.CARDS / f"{p['id']}.png").exists()}
        fresh = dict(list(fresh.items())[:24])
    return fresh, db, made


def ensure_card(p, fresh):
    """Card image path for a player; builds it from RenderZ if we don't have it yet."""
    path = renderz.CARDS / f"{p['id']}.png"
    if not path.exists():
        src = fresh.get(str(p["id"]))
        if not src or not src.get("img_bg"):
            return None
        renderz.CARDS.mkdir(parents=True, exist_ok=True)
        if src.get("source") == "fcmobileforum":
            from fmm import fmf
            fmf.build_card(src).save(path)
        else:
            renderz.build_card(src).save(path)
    return str(path)


def trend_boost():
    """Player names trending on YouTube right now -> mention counts (refreshed before every build)."""
    try:
        from fmm import trends
        t = trends.run()
        print("trending:", t["topics"][:4], t["players"][:5])
        return {n.lower(): c for n, c in t["players"]}
    except Exception as ex:
        print("trend check skipped:", str(ex)[:100])
        return {}


def pick(kind, fresh, db, state):
    pool = list(db.values())
    hot = trend_boost()
    heat = lambda p: hot.get((p.get("name") or "").lower(), 0)
    key = lambda p: f"{p.get('name')}|{p.get('ovr')}|{p.get('pos')}"  # same card on RenderZ and the forum
    done = set(state["featured"])
    unfeatured = sorted([p for p in fresh.values() if str(p["id"]) not in done and key(p) not in done],
                        key=lambda p: (heat(p), p.get("added") or "", p.get("ovr") or 0), reverse=True)
    weekday = dt.datetime.now().weekday()
    if unfeatured:
        p = unfeatured[0]
        return ("review_reel" if kind == "reel" else "review_post"), [p], pool
    latest = sorted(fresh.values(), key=lambda p: (heat(p), p.get("ovr") or 0), reverse=True)
    if kind == "reel":
        return ("tierlist" if weekday % 2 else "countdown"), latest[:8], pool
    # photo fallback rotates daily: card battle -> guess the player -> rate this card
    rot = ["versus", "guess", "rate"][dt.date.today().toordinal() % 3]
    if rot != "versus":
        used = set(state.get("used_photo", []))
        cand = [p for p in latest if str(p["id"]) not in used] or latest
        return rot, [cand[0]], pool
    by_group = {}
    for p in latest:
        by_group.setdefault(rv.group(p["pos"]), []).append(p)
    pair = max(by_group.values(), key=len)[:2]
    return "versus", pair, pool


def build_from_inbox(slot):
    """Any slot: your own gameplay from the Drive clips folder, when there is any."""
    try:
        from fmm import inbox
        got = inbox.next_clip()
    except Exception as ex:
        print("clips inbox skipped:", str(ex)[:120])
        return False
    if not got:
        return False
    mp4, title, src = got
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy(mp4, OUT / "slot.mp4")
    cover = Path(mp4).with_name(Path(mp4).stem + "_cover.jpg")
    if cover.exists():
        shutil.copy(cover, OUT / "slot_cover.jpg")
    caption = (f"⚽ {title.title()}\n\nWould you have scored this? Rate it 1–10 👇\n\n"
               "Follow FMM for daily FC Mobile goals, cards & codes 🔔\n\n"
               "#FCMobile #FCMobile26 #EASportsFCMobile #FCMobileGoals #Gaming #FMM")
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({"slot": slot, "kind": "reel", "type": "clip",
                                                   "media": "slot.mp4", "source": src}, indent=1), encoding="utf-8")
    print("built clip from", src)
    return True


def build(slot):
    from fmm import brand, motion
    if build_from_inbox(slot):  # your own gameplay always goes first, in any slot
        return
    kind = SLOTS[slot]
    state = load_state()
    fresh, db, made = latest_players()
    ctype, players, pool = pick(kind, fresh, db, state)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for p in players:
        p["card"] = ensure_card(p, fresh)
    players = [p for p in players if p.get("card")]
    if not players:
        print("no usable cards this time"); return
    p = players[0]
    r = rv.review(p, pool)
    if ctype == "review_post":
        post = {"id": "slot", "type": "review", "tag": "New Card Review", "player": p["name"],
                "subtitle": f"{p['ovr']} OVR • {p['pos']}", "card": p["card"], "tier": "gold",
                "pros": r["pros"], "cons": r["cons"], "score": r["score"]}
        media, caption = brand.render(post, OUT), r["caption"]
    elif ctype == "review_reel":
        cover_text = {"MUST BUY": "MUST BUY?!", "WORTH IT": "WORTH IT?", "SITUATIONAL": "BUY OR NOT?",
                      "SKIP": "DON'T BUY!?"}[r["verdict"]]
        reel = {"id": "slot", "cover": {"subject": p["card"], "text": cover_text, "sub": f"{p['ovr']} OVR {p['name']}",
                                         "color": "green" if r["score"] >= 9 else "red"},
                "scenes": [
            {"scene": "reveal", "title": "New Card", "sub": f"{p['ovr']} OVR {p['name']}", "card": p["card"]},
            {"scene": "stamp", "title": f"FMM Rating {r['score']}/10", "text": r["verdict"],
             "color": list(VERDICT_COLOR[r["verdict"]]), "card": p["card"]}]}
        media, caption = motion.render_reel(reel, OUT), r["caption"]
    elif ctype == "countdown":
        reel = {"id": "slot", "cover": {"subject": players[0]["card"], "text": f"TOP {min(7, len(players))}\nNEW CARDS",
                                         "sub": f"#1 IS {players[0]['ovr']} OVR!", "color": "gold"},
                "scenes": [{"scene": "countdown", "position": "NEW CARDS",
                                           "players": [{"name": x["name"], "card": x["card"]} for x in players[:7]][::-1]}]}
        media = motion.render_reel(reel, OUT)
        caption = (f"🔥 Top {min(7, len(players))} newest FC Mobile cards right now\n\n"
                   + "\n".join(f"{i + 1}. {x['ovr']} {x['pos']} {x['name']}" for i, x in enumerate(players[:7]))
                   + "\n\n👇 Which one are you getting?\n\n#FCMobile #FCMobile26 #EASportsFCMobile #FCMobileCards #FMM")
    elif ctype == "tierlist":
        scored = sorted(((rv.review(x, pool)["score"], x) for x in players), key=lambda t: -t[0])
        tiers = {"S": [], "A": [], "B": [], "C": []}
        for s, x in scored:
            tiers["S" if s >= 9 else "A" if s >= 8 else "B" if s >= 7 else "C"].append(x["card"])
        reel = {"id": "slot", "cover": {"subject": scored[0][1]["card"], "text": "TIER LIST!", "sub": "WHO'S S TIER?",
                                         "color": "purple"},
                "scenes": [{"scene": "tierlist", "title": "New Cards Tier List",
                                           "tiers": {k: v for k, v in tiers.items() if v}}]}
        media = motion.render_reel(reel, OUT)
        caption = ("📊 FMM tier list: this week's new FC Mobile cards\n\n"
                   + "\n".join(f"{t}: " + ", ".join(f"{x['name']} {x['ovr']}" for s, x in scored
                                                    if (t == 'S' and s >= 9) or (t == 'A' and 8 <= s < 9)
                                                    or (t == 'B' and 7 <= s < 8) or (t == 'C' and s < 7))
                             for t in "SABC")
                   + "\n\n👇 Agree or disagree? Tell us who's misplaced!\n\n#FCMobile #FCMobile26 #TierList #FMM")
    elif ctype == "guess":
        hints = [f"{p['ovr']} OVR", p["pos"], p.get("nation") or "", p.get("club") or ""]
        post = {"id": "slot", "type": "guess", "card": p["card"], "hints": [h for h in hints if h][:4]}
        media = brand.render(post, OUT)
        caption = ("🤔 GUESS THE PLAYER!\n\nHints are on the card. First correct answer gets a shout-out 🏆\n"
                   "Answer in our next post 👇\n\n#FCMobile #FCMobile26 #GuessThePlayer #FMM")
        state.setdefault("used_photo", []).append(str(p["id"]))
        state.setdefault("reveal", []).append({"name": p["name"], "ovr": p["ovr"], "date": dt.date.today().isoformat()})
    elif ctype == "rate":
        post = {"id": "slot", "type": "rate", "card": p["card"]}
        media = brand.render(post, OUT)
        caption = (f"⭐ Rate {p['ovr']} OVR {p['name']} ({p['pos']}) from 1 to 10!\n\n"
                   "Be honest — is he worth the hype? 👇\n\n#FCMobile #FCMobile26 #RateTheCard #FMM")
        state.setdefault("used_photo", []).append(str(p["id"]))
    else:  # versus
        a, b = players[0], players[1] if len(players) > 1 else players[0]
        post = {"id": "slot", "type": "versus", "tag": "Which one would you pick?",
                "title": f"{a['name']} or {b['name']}?", "cards": [{"card": a["card"]}, {"card": b["card"]}]}
        media = brand.render(post, OUT)
        caption = (f"⚔️ {a['ovr']} {a['name']} ({a['pos']}) vs {b['ovr']} {b['name']} ({b['pos']})\n\n"
                   f"Only one goes in your starting XI. Who's your pick and why? 👇\n\n"
                   f"#FCMobile #FCMobile26 #EASportsFCMobile #CardBattle #FMM")
    pending = [r for r in state.get("reveal", []) if not r.get("done")]
    if pending and ctype != "guess":  # answer to the last "guess the player"
        r = pending[-1]
        caption = f"✅ Last 'Guess the Player' answer: {r['ovr']} OVR {r['name']}! Did you get it?\n\n" + caption
        for x in pending:
            x["done"] = True
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    manifest = {"slot": slot, "kind": kind, "type": ctype, "media": Path(media).name,
                "players": [x["id"] for x in players], "built": dt.datetime.now().isoformat(timespec="minutes")}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    if ctype.startswith("review"):
        state["featured"] += [str(p["id"]), f"{p.get('name')}|{p.get('ovr')}|{p.get('pos')}"]
    state["history"] = (state["history"] + [manifest])[-200:]
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    print("built", manifest)


def post():
    from fmm import poster
    m = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    caption = (OUT / "caption.txt").read_text(encoding="utf-8")
    kind = "reel" if m["media"].endswith(".mp4") else "photo"
    print("posted", poster.post(kind, OUT / m["media"], caption, "both"))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build":
        build(a[1] if len(a) > 1 else "1300")
    elif a and a[0] == "post":
        post()
