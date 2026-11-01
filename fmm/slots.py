"""The 4 daily FMM posting slots (Bangladesh time).

    python -m fmm.slots build <slot>   -> 30 min before: check RenderZ, pick + render content into output/slot/
    python -m fmm.slots post           -> at slot time: publish output/slot/ to FB + IG (+ YouTube for Reels)

Slots (BDT): 0700 (USA evening, Reel) · 1300 (Asia lunch, photo) · 1900 (Indonesia 20:00 WIB, photo) · 2100 (BD/India peak, Reel)
New cards are featured first (newest/highest OVR); with nothing new, slots fall back to card battles,
tier lists and countdowns built from the latest cards.
"""
import datetime as dt, json, shutil, subprocess, sys
from pathlib import Path

from fmm import renderz, review as rv

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "slot"
STATE = ROOT / "content" / "featured.json"
SLOTS = {"0700": "reel", "1300": "photo", "1900": "photo", "2100": "reel"}  # FC Mobile is biggest in South/SE Asia; 07:00 keeps one high-pay US slot
VERDICT_COLOR = {"MUST BUY": (0, 200, 83), "WORTH IT": (255, 215, 0), "SITUATIONAL": (255, 152, 0), "SKIP": (225, 6, 44)}


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"featured": [], "history": []}


_TRENDS = {}


def confirmed_only(cards):
    """Cross-check rule: use a card only if its program is confirmed by a second source
    (FC Mobile creators' YouTube videos from the last 48h) and not on the manual hold list."""
    from fmm import trends
    if "t" not in _TRENDS:
        try:
            _TRENDS["t"] = trends.run()
        except Exception as ex:
            print("cross-check unavailable, using last saved trends:", str(ex)[:80])
            _TRENDS["t"] = trends.load()
    seen = _TRENDS["t"].get("programs_seen", [])
    st = load_state()
    hold, verified = set(st.get("hold_programs", [])), set(st.get("confirmed_programs", []))
    keep, held = {}, set()
    for k, p in cards.items():
        prog = (p.get("program") or "").replace("PROGRAM_", "")
        if prog in hold or (prog not in verified and not trends.program_confirmed(prog, seen)):
            held.add(prog)
        else:
            keep[k] = p
    if held:
        print("held back (not confirmed by a 2nd source yet):", sorted(held))
    return keep


def latest_players():
    """Fresh list from RenderZ when reachable; otherwise (cloud is blocked by RenderZ) the cards
    your PC already collected into the repo: players_db.json + assets/cards/rz/*.png."""
    made = []
    try:
        made = renderz.run()
        page = renderz.fetch(renderz.LIST_URL).decode("utf-8", "ignore")
        fresh = {str(p["id"]): p for p in (renderz.slim(x) for x in renderz.extract_array(page))}
        # RenderZ is an independent 2nd source: whatever it lists counts as verified
        st = load_state()
        progs = {(p.get("program") or "").replace("PROGRAM_", "") for p in fresh.values()} - {""}
        st["confirmed_programs"] = sorted(set(st.get("confirmed_programs", [])) | progs)
        STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    except Exception as ex:
        print("RenderZ not reachable here:", str(ex)[:80])
        fresh = None
    db = json.loads(renderz.DB.read_text(encoding="utf-8"))["players"] if renderz.DB.exists() else {}
    if fresh is None:  # cloud: fcmobileforum.com allows it
        try:
            from fmm import fmf
            fresh = {p["id"]: p for p in fmf.latest()}  # all listed; held programs are filtered out below
            for pid, p in fresh.items():
                db.setdefault(pid, {k: v for k, v in p.items() if not k.startswith("img_")})
            renderz.DB.write_text(json.dumps({"players": db}, ensure_ascii=False, indent=0), encoding="utf-8")
            print(f"fcmobileforum: {len(fresh)} latest cards")
            fresh = confirmed_only(fresh)
        except Exception as ex:
            print("fcmobileforum not reachable, using collected cards:", str(ex)[:80])
    fresh = confirmed_only(fresh) if fresh is not None else None
    if fresh is None:
        recent = sorted(db.values(), key=lambda p: p.get("added") or "", reverse=True)
        fresh = {str(p["id"]): p for p in recent if (renderz.CARDS / f"{p['id']}.png").exists()}
        fresh = confirmed_only(dict(list(fresh.items())[:40]))
    # one entry per card: the forum lists some cards several times under different ids
    uniq, keys = {}, set()
    for k, p in fresh.items():
        key = f"{p.get('name')}|{p.get('ovr')}|{p.get('pos')}"
        if key not in keys:
            keys.add(key); uniq[k] = p
    return uniq, db, made


PROGRAM_NAMES = {"BD": "Ballon d'Or", "TOTW": "Team of the Week", "ICONS": "Icons", "HEROS": "Heroes",
                 "HOFS": "Hall of Fame", "TOTY": "TOTY", "TOTS": "TOTS", "UCL": "Champions League",
                 "SCR": "Scream Team", "MLS": "MLS", "TWG": "World's Game", "OUTSTANDING": "Outstanding",
                 "ANN": "Anniversary", "CHAMPIONS": "Champions", "NUMERO": "Numero Uno", "SIG": "Signature"}


def program_name(code):
    import re as _re
    c = _re.sub(r"^(PROGRAM_?|PROGRAMNAME_?)", "", code or "", flags=_re.I).upper()
    fam = _re.sub(r"\d+$", "", c)
    return next((v for k, v in PROGRAM_NAMES.items() if fam.startswith(k)), fam.replace("_", " ").title() or "New")


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
        t = _TRENDS.get("t") or trends.run()
        print("trending:", t["topics"][:4], t["players"][:5])
        return {n.lower(): c for n, c in t["players"]}
    except Exception as ex:
        print("trend check skipped:", str(ex)[:100])
        return {}


_SLOT = {"v": None}


def slot_now():
    return _SLOT["v"]


def pick(kind, fresh, db, state):
    pool = list(db.values())
    hot = trend_boost()
    from fmm.versions import FOCUS  # CR7, Messi, Neymar, Kane, BD & Indian players: always near the front
    heat = lambda p: hot.get((p.get("name") or "").lower(), 0) + \
        (5 if any(f in (p.get("name") or "").lower() for f in FOCUS) else 0)
    key = lambda p: f"{p.get('name')}|{p.get('ovr')}|{p.get('pos')}"  # same card on RenderZ and the forum
    done = set(state["featured"])
    unfeatured = sorted([p for p in fresh.values() if str(p["id"]) not in done and key(p) not in done],
                        key=lambda p: (heat(p), p.get("added") or "", p.get("ovr") or 0), reverse=True)
    weekday = dt.datetime.now().weekday()
    week_ago = (dt.datetime.now(dt.UTC) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    this_week = [p for p in fresh.values() if (p.get("added") or "") >= week_ago]
    # one-off override for one dated slot, e.g. {"2026-11-05-0700": "countdown"}: applies once, nothing to delete
    # (state saves merge and can't remove keys, so an undated override would repeat every day)
    force = state.get("force", {}).get(f"{dt.date.today().isoformat()}-{slot_now()}")
    if force in ("countdown", "tierlist") and this_week:
        return force, sorted(this_week, key=lambda p: (p.get("ovr") or 0, heat(p)), reverse=True)[:8], pool
    wk_unf = sorted([p for p in unfeatured if p in this_week], key=lambda p: (heat(p), p.get("ovr") or 0), reverse=True)
    unfeatured = wk_unf or unfeatured  # this week's cards first: trending, then highest OVR
    if kind == "photo":  # photo slots rotate formats; the "review" turn reviews the next new card
        ROT = ["review_post", "rank10", "versus", "pick3", "guess", "rank10", "compare4", "xi", "rate", "gem", "worth", "meme"]
        n = state.get("photo_n", 0)
        state["photo_n"] = n + 1
        ROT = [r for r in ROT if r != state.get("drop")] + [state["boost"]] * 2 if state.get("boost") else             [r for r in ROT if r != state.get("drop")]  # weekly growth loop: more of the best format, none of the worst
        rot = ROT[n % len(ROT)]
        if rot == "review_post":
            if unfeatured:
                return "review_post", [unfeatured[0]], pool
            rot = "versus"
        unfeatured = []  # fall through to the format below
        forced_rot = rot
    else:
        forced_rot = None
    if unfeatured:
        p = unfeatured[0]
        return ("review_reel" if kind == "reel" else "review_post"), [p], pool
    base_set = this_week if len(this_week) >= 5 else list(fresh.values())
    latest = sorted(base_set, key=lambda p: (heat(p), p.get("ovr") or 0), reverse=True)
    if kind == "reel":
        return ("tierlist" if weekday % 2 else "countdown"), latest[:8], pool
    rot = forced_rot or "versus"
    if rot in ("xi", "gem", "worth", "meme", "compare4", "pick3", "rank10"):
        return rot, latest, pool
    if rot == "versus":
        return "versus", next_pair(latest, state, pool), pool
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
    # evergreen Shorts are titled like "Prime Neymar penalty☠️🔥": player + moment + emoji, nothing tied to an event
    name = Path(src).stem.strip()
    caption = (f"{name.title() if len(name) <= 40 else title.title()} ☠️🔥\n\nWould you have scored this? Rate it 1–10 👇\n\n"
               "Follow FMM for daily FC Mobile goals, cards & codes 🔔\n\n"
               "#FCMobile #FIFAMobile #EAFC #FCMobileGoals #Gaming #FMM")
    (OUT / "caption.txt").write_text(caption, encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({"slot": slot, "kind": "reel", "type": "clip",
                                                   "media": "slot.mp4", "source": src}, indent=1), encoding="utf-8")
    print("built clip from", src)
    return True


PACK_CAPTION = ROOT / "content" / "pack_caption.txt"


def build_pack(got=None, title=None, caption=None):
    """Pack-opening Reel from a Drive video named 'pack ….mp4' (e.g. 'pack opening ronaldo.mp4' -> title + card)."""
    try:
        from fmm import inbox, clips, sfx, thumb
        got = got or inbox.pack_video()
        if not got:
            return False
        f, src = got
        who = Path(f["name"]).stem.lower().replace("pack opening", "").replace("pack", "").strip(" -_")
        title = title or (f"I PACKED {who.upper()}!!" if who else "PACK OPENING!!")
        card = inbox.scorer_card(f["name"])
        if OUT.exists():
            shutil.rmtree(OUT)
        OUT.mkdir(parents=True)
        ov = clips.overlay_png(title, "PACK OPENING TRICK IN CAPTION", OUT / "ov.png", card)
        dur = clips.duration(src)
        lv = clips.loudness(src)  # biggest moment = the reveal
        reveal = max(lv, key=lambda x: x[1])[0] if lv else dur * 0.6
        start = max(0.0, reveal - 10)  # keep ~15 s: build-up, reveal, card on screen
        dur = min(dur, reveal + 5) - start
        reveal -= start
        sfx.build()
        ms = int(max(0.0, reveal - 0.2) * 1000)
        vf = ("[0:v]split=2[a][b];[a]scale=-2:1920,crop=1080:1920,boxblur=25:2,eq=brightness=-0.15:saturation=1.3[bg];"
              "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2-40[base];[base][1:v]overlay=0:0,format=yuv420p[v]")
        af = (f"[2:a]volume=0.8[r];[3:a]adelay={ms}|{ms}[i];[4:a]adelay={ms}|{ms}[s];"
              f"[r][i][s]amix=inputs=3:normalize=0,apad,atrim=0:{dur:.2f},loudnorm=I=-14:TP=-1.5[a]")
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", str(src), "-i", str(ov), "-i", str(sfx.OUT / "riser.wav"),
                            "-i", str(sfx.OUT / "impact.wav"), "-i", str(sfx.OUT / "sparkle.wav"),
                            "-filter_complex", vf + ";" + af, "-map", "[v]", "-map", "[a]", "-t", f"{dur:.2f}", "-r", "30",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                            "-movflags", "+faststart", str(OUT / "slot.mp4")], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(r.stderr[-300:])
        frame = OUT / "frame.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(max(0.0, start + dur - 3)), "-i", str(src),  # packed card is on screen at the end
                        "-frames:v", "1", "-vf", "crop=ih*3/4:ih:(iw-ih*3/4)/2:0", str(frame)])
        thumb.cover(card or (str(frame) if frame.exists() else None), title.replace("I PACKED ", "I PACKED\n", 1) if len(title) > 16 else title,
                    OUT / "slot_cover.jpg", sub="PACK OPENING", color="gold", bg=str(frame) if card and frame.exists() else None)
        ov.unlink(missing_ok=True); frame.unlink(missing_ok=True)
        caption = caption or PACK_CAPTION.read_text(encoding="utf-8").replace("{title}", title.title())
        inbox.mark_pack(f)
        finish("2100", "reel", "pack", OUT / "slot.mp4", caption, [], load_state())
        return True
    except Exception as ex:
        print("pack Reel skipped:", str(ex)[:150])
        return False


def build_versions(slot):
    """Two versions of one player (GOAT vs WASTE) over your meme clip. Needs a 'meme…' video in the Drive folder."""
    st = load_state()
    st["reel_n"] = st.get("reel_n", 0) + 1
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    if st["reel_n"] % 2:
        return False
    try:
        from fmm import versions, inbox
        used = set(st.get("used_versions", []))
        # new cards of this week vs their old versions (only clear stat gaps); nothing worth it -> normal Reel
        fresh, _, _ = latest_players()
        week_ago = (dt.datetime.now(dt.UTC) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
        new = [p for p in fresh.values() if (p.get("added") or "") >= week_ago]
        pr = next((p for p in versions.new_vs_old(new) if p["irony"] and p["name"] not in used
                   and confirmed_only({"g": p["good"], "b": p["bad"]}).keys() == {"g", "b"}
                   and all((renderz.CARDS / f"{c['id']}.png").exists() or ensure_card(c, fresh) for c in (p["good"], p["bad"]))),
                  None)
        if not pr:
            return False
        meme = inbox.meme_clip()
        if not meme:
            print("EA-logic Reel skipped: upload a meme clip named 'meme ….mp4' to the Drive folder")
            return False
        if OUT.exists():
            shutil.rmtree(OUT)
        versions.make_reel(pr, meme, OUT)
        (OUT / "caption.txt").write_text(versions.caption(pr), encoding="utf-8")
        st = load_state()
        st.setdefault("used_versions", []).append(pr["name"])
        finish(slot, "reel", "versions", OUT / "slot.mp4", versions.caption(pr), [pr["good"], pr["bad"]], st)
        return True
    except Exception as ex:
        print("EA-logic Reel skipped:", str(ex)[:150])
        return False


def build(slot):
    from fmm import brand, motion
    _SLOT["v"] = slot
    if slot == "2100" and dt.datetime.now().weekday() in (3, 6) and build_pack():  # Thu + Sun: pack opening Reel
        return
    if build_from_inbox(slot):  # your own gameplay always goes first, in any slot
        return
    if SLOTS[slot] == "reel" and build_versions(slot):  # every 2nd Reel: "EA Sports Logic"
        return
    kind = SLOTS[slot]
    state = load_state()
    fresh, db, made = latest_players()
    ctype, players, pool = pick(kind, fresh, db, state)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    if ctype in ("xi", "gem", "worth", "meme", "compare4", "pick3", "rank10"):
        media, caption = build_extra(ctype, players, pool, fresh, state)
        return finish(slot, kind, ctype, media, caption, players[:1], state)
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
                "pros": r["short_pros"], "cons": r["short_cons"], "score": r["score"],
                "verdict": r["verdict"], "group": r["group"], "info": p, "pool": pool}
        media, caption = brand.render(post, OUT), r["caption"]
    elif ctype == "review_reel":
        cover_text = {"MUST BUY": "THIS CARD\nIS BROKEN!!", "WORTH IT": "WORTH IT?!", "SITUATIONAL": "BUY OR NOT?",
                      "SKIP": "DON'T BUY\nTHIS!!"}[r["verdict"]]
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
        caption = (f"🔥 This week's new FC Mobile players — top {min(7, len(players))} by OVR\n\n"
                   + "\n".join(f"{i + 1}. {x['ovr']} {x['pos']} {x['name']}" for i, x in enumerate(players[:7]))
                   + "\n\n👇 Which one are you getting?\n\n#FCMobile #FIFAMobile #EAFC #FCMobileCards #FMM")
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
    else:  # versus -> full stats comparison (reference: assets/references/vs_1v1_stats.png)
        a, b = players[0], players[1] if len(players) > 1 else players[0]
        for x in (a, b):
            x["program_name"] = program_name(x.get("program"))
        media = brand.render({"id": "slot", "type": "compare", "a": a, "b": b}, OUT)
        caption = (f"⚔️ {a['ovr']} {a['name']} ({a['pos']}) vs {b['ovr']} {b['name']} ({b['pos']})\n\n"
                   f"Only one goes in your starting XI. Who's your pick and why? 👇\n\n"
                   f"#FCMobile #FIFAMobile #EAFC #CardBattle #FMM")
    if ctype.startswith("review"):
        state["featured"] += [str(p["id"]), f"{p.get('name')}|{p.get('ovr')}|{p.get('pos')}"]
    finish(slot, kind, ctype, media, caption, players, state)


def finish(slot, kind, ctype, media, caption, players, state):
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
    state["history"] = (state["history"] + [manifest])[-200:]
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    print("built", manifest)


XI_SLOTS = [("gk", 1), ("def", 4), ("mid", 3), ("att", 3)]
MEMES = [("When you finally pack {name}", "When you check his weak foot"),
         ("Me saving gems for 3 weeks", "EA dropping {ovr} OVR {name} on Thursday"),
         ("{name} on paper: {ovr} OVR", "{name} in my squad after 5 losses"),
         ("Opponent's {name}", "My {name}"),
         ("Me: one more pack", "Me 2 hours later, still no {name}")]
TAGS = "#FCMobile #FIFAMobile #EAFC #FMM"


def next_pair(latest, state, pool=()):
    """A new card vs the best card at the exact same position (old cards count), never a pair battled before.
    Owner rule: never compare players with different positions."""
    used = set(state.get("used_pairs", []))
    pool = confirmed_only({str(p["id"]): p for p in pool}).values()  # cross-check rule applies to old cards too
    rivals = [p for p in list(latest) + list(pool) if (renderz.CARDS / f"{p['id']}.png").exists() or p.get("img_bg")]
    times = lambda p: sum(p["name"] in k.split("|") for k in used)
    for p in sorted(latest, key=times):  # least-battled new card first (stable: keeps newest/trending order)
        same = sorted([q for q in rivals if q.get("pos") == p.get("pos") and q["name"] != p["name"]],
                      key=lambda q: -(q.get("ovr") or 0))
        for q in same:
            key = "|".join(sorted([p["name"], q["name"]]))
            if key not in used:
                state.setdefault("used_pairs", []).append(key)
                return [p, q]
    return []


def render_versus(pair, fresh):
    from fmm import brand
    a, b = pair[0], pair[1] if len(pair) > 1 else pair[0]
    for x in (a, b):
        x["card"] = x.get("card") or ensure_card(x, fresh)
        x["program_name"] = program_name(x.get("program"))
    post = {"id": "slot", "type": "compare", "a": a, "b": b}
    caption = (f"⚔️ {a['ovr']} {a['name']} ({a['pos']}) vs {b['ovr']} {b['name']} ({b['pos']})\n\n"
               f"Only one goes in your starting XI. Who's your pick and why? 👇\n\n"
               f"#FCMobile #FIFAMobile #EAFC #CardBattle #FMM")
    return brand.render(post, OUT), caption


def build_extra(ctype, latest, pool, fresh, state):
    """Best Budget XI, Hidden Gem, Is the event worth it?, memes."""
    from fmm import brand
    import random
    for p in list(fresh.values())[:24]:  # make sure the latest cards all have images
        try:
            ensure_card(p, fresh)
        except Exception as ex:
            print("card skipped", p.get("name"), str(ex)[:60])
    have, names = [], set()
    pool = list(confirmed_only({str(p.get("id")): p for p in pool}).values())  # cross-check applies here too
    for p in sorted(pool, key=lambda p: p.get("added") or "", reverse=True):  # one card per player (newest)
        if p.get("stats") and (renderz.CARDS / f"{p['id']}.png").exists() and p.get("name") not in names:
            names.add(p.get("name"))
            have.append({**p, "card": str(renderz.CARDS / f"{p['id']}.png")})
    rnd = random.Random(dt.date.today().toordinal())
    if ctype == "xi":
        ovrs = sorted(p["ovr"] for p in have if p.get("ovr"))
        cap = ovrs[len(ovrs) // 4] if ovrs else 999          # budget = the cheaper quarter of the cards we know
        cheap = [p for p in have if (p.get("ovr") or 0) <= cap]
        team, used = [], set()
        for g, n in XI_SLOTS:
            best = sorted([p for p in cheap if rv.group(p.get("pos", "")) == g and p["id"] not in used],
                          key=lambda p: -rv.key_avg(p, g))[:n]
            if g != "gk" and len(best) < n:  # short on this line: next-best outfield cards fill in
                spare = sorted([p for p in cheap if p["id"] not in used and p not in best and rv.group(p.get("pos", "")) != "gk"],
                               key=lambda p: -(p.get("ovr") or 0))
                best += spare[:n - len(best)]
            used |= {p["id"] for p in best}
            team += best + [{"name": "?", "ovr": "", "pos": g.upper()}] * (n - len(best))
        if sum(1 for p in team if p.get("name") != "?") < 8:  # too few cards known yet
            return render_versus(next_pair(latest, state, pool), fresh)
        post = {"id": "slot", "type": "xi", "title": "Best Budget XI", "subtitle": f"Every card {cap} OVR or lower",
                "players": team}
        lines = [f"{p.get('pos', '')} {p.get('name')} {p.get('ovr')}" for p in team if p.get("name") != "?"]
        caption = (f"💰 FMM BEST BUDGET XI (all {cap} OVR or lower)\n\n" + "\n".join(lines)
                   + "\n\nWho would you swap in? 👇 Save this for your next rebuild 📌\n\n" + TAGS + " #BudgetSquad")
    elif ctype == "gem":
        def gem_score(p):
            g = rv.group(p.get("pos", ""))
            peers = [x for x in have if rv.group(x.get("pos", "")) == g]
            pct = sum(rv.key_avg(x, g) <= rv.key_avg(p, g) for x in peers) / max(1, len(peers))
            low = sum((x.get("ovr") or 0) >= (p.get("ovr") or 0) for x in peers) / max(1, len(peers))
            return pct + low
        used = set(state.get("used_photo", []))
        top_ovr = max((x.get("ovr") or 0) for x in have)
        cands = [x for x in have if str(x["id"]) not in used and (x.get("ovr") or 0) < top_ovr - 2]
        if not cands:  # nothing "low OVR" to talk about yet -> a card battle instead
            return render_versus(next_pair(latest, state, pool), fresh)
        p = max(cands, key=gem_score)
        g = rv.group(p.get("pos", ""))
        labels = [(renderz.STAT_NAMES.get(k, k), p["stats"][k]) for k in sorted(
            [k for k in rv.GROUPS[g]["keys"] if k in p["stats"]], key=lambda k: -p["stats"][k])[:5]]
        post = {"id": "slot", "type": "gem", "card": p["card"], "subtitle": f"{p['ovr']} OVR {p['name']} • {p['pos']}",
                "stats": labels}
        state.setdefault("used_photo", []).append(str(p["id"]))
        caption = (f"💎 HIDDEN GEM: {p['ovr']} OVR {p['name']} ({p['pos']})\n\nLow OVR, but his key stats beat many "
                   f"higher-rated cards:\n" + "\n".join(f"• {l}: {v}" for l, v in labels)
                   + "\n\nWould you give him a chance? 👇\n\n" + TAGS + " #HiddenGem")
    elif ctype == "worth":
        by_prog = {}
        for p in latest:
            by_prog.setdefault(p.get("program") or "NEW", []).append(p)
        prog, cards = max(by_prog.items(), key=lambda kv: len(kv[1]))
        seen_names, uniq = set(), []
        for p in sorted(cards, key=lambda p: -(p.get("ovr") or 0)):
            if p.get("name") in seen_names:
                continue
            p["card"] = ensure_card(p, fresh)
            if p.get("card"):
                seen_names.add(p.get("name")); uniq.append(p)
        cards = uniq[:5]
        scores = [rv.review(p, pool)["score"] for p in cards]
        avg = sum(scores) / max(1, len(scores))
        verdict = "WORTH IT" if avg >= 8 else "SITUATIONAL" if avg >= 7 else "SKIP"
        name = program_name(prog)
        post = {"id": "slot", "type": "worth", "event": name, "cards": [p["card"] for p in cards], "verdict": verdict,
                "note": f"Average FMM rating of its top cards: {avg:.1f}/10"}
        caption = (f"🤔 Is the {name} event worth your gems?\n\nTop cards:\n"
                   + "\n".join(f"• {p['ovr']} {p['name']} ({p['pos']}) — {s}/10" for p, s in zip(cards, scores))
                   + f"\n\nFMM verdict: {verdict}\n\nAre you spending? 👇\n\n" + TAGS)
    elif ctype == "rank10":  # weekly Top 10 per position from fcmobileforum.com/top-20 (cross-checked)
        from fmm import top20
        n = state.get("rank_n", 0); state["rank_n"] = n + 1
        pos = top20.POSITIONS[n % len(top20.POSITIONS)]
        ten = top20.ensure_images(top20.top10(pos))
        if len(ten) < 6:
            return render_versus(next_pair(latest, state, pool), fresh)
        post = {"id": "slot", "type": "top10", "position": pos.upper(), "title": "This week",
                "players": [{"name": p["name"], "card": p["card"], "ovr": p.get("ovr")} for p in ten]}
        nl = "\n"
        caption = (f"🏆 TOP 10 {pos.upper()} in FC Mobile this week{nl}{nl}"
                   + nl.join(f"{i + 1}. {p.get('ovr')} {p['name']} ({program_name(p.get('program'))})"
                             for i, p in enumerate(ten))
                   + f"{nl}{nl}Who's missing? 👇 Save this for your next upgrade 📌{nl}{nl}" + TAGS + f" #Top10 #{pos.upper()}")
    elif ctype == "compare4":  # Top 4 of the position with the most confirmed cards (ref: vs_top4_table.png)
        by_pos = {}
        for p in have:
            by_pos.setdefault(p.get("pos"), []).append(p)
        pos, cards = max(by_pos.items(), key=lambda kv: (len(kv[1]) >= 4, len(kv[1])))
        if len(cards) < 3:
            return render_versus(next_pair(latest, state, pool), fresh)
        top4 = sorted(cards, key=lambda p: (p.get("ovr") or 0, rv.key_avg(p, rv.group(pos))), reverse=True)[:4]
        post = {"id": "slot", "type": "compare4", "position": pos, "players": top4}
        from fmm.review import face_stats
        caption = (f"📊 Top {len(top4)} {pos} cards right now — stats compared\n\n"
                   + "\n".join(f"• {p['ovr']} {p['name']}: " + " ".join(f"{k} {v}" for k, v in face_stats(p).items())
                               for p in top4)
                   + "\n\nWho's your #1? 👇\n\n" + TAGS + f" #{pos}")
    elif ctype == "pick3":  # Pick one of 3 cards from the same event (ref: pick_one_react.png)
        used = set(state.get("used_photo", []))
        by_prog = {}
        for p in latest:
            if str(p["id"]) not in used:
                by_prog.setdefault(p.get("program") or "", []).append(p)
        prog, cards = max(by_prog.items(), key=lambda kv: len(kv[1])) if by_prog else ("", latest)
        three = sorted(cards, key=lambda p: -(p.get("ovr") or 0))[:3]
        for p in three:
            p["card"] = p.get("card") or ensure_card(p, fresh)
            state.setdefault("used_photo", []).append(str(p["id"]))
        three = [p for p in three if p.get("card")]
        if len(three) < 3:
            return render_versus(next_pair(latest, state, pool), fresh)
        ev = program_name(prog)
        post = {"id": "slot", "type": "pick3", "title": "Pick one", "subtitle": f"{three[0]['ovr']} OVR {ev}",
                "cards": [p["card"] for p in three]}
        caption = (f"🎁 You can only pick ONE {ev} card:\n\n❤️ {three[0]['ovr']} {three[0]['name']}\n"
                   f"😮 {three[1]['ovr']} {three[1]['name']}\n😆 {three[2]['ovr']} {three[2]['name']}\n\n"
                   f"Which one and why? 👇\n\n" + TAGS)
    else:  # meme
        cand = sorted([p for p in latest if p.get("card") or ensure_card(p, fresh)], key=lambda p: -(p.get("ovr") or 0))
        p = cand[0] if cand else have[0]
        p["card"] = p.get("card") or ensure_card(p, fresh)
        top, bottom = rnd.choice(MEMES)
        post = {"id": "slot", "type": "meme", "top": top.format(**p), "bottom": bottom.format(**p), "card": p["card"]}
        caption = f"😂 Be honest… who else? 👇\n\n{TAGS} #FCMobileMemes"
    media = brand.render(post, OUT)
    return media, caption


def post():
    from fmm import poster
    m = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    caption = (OUT / "caption.txt").read_text(encoding="utf-8")
    kind = "reel" if m["media"].endswith(".mp4") else "photo"
    print("posted", poster.post(kind, OUT / m["media"], caption, "both", m.get("type")))  # type feeds the weekly growth loop


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "build":
        build(a[1] if len(a) > 1 else "1300")
    elif a and a[0] == "post":
        post()
