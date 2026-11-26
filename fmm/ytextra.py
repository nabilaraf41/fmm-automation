"""YouTube-only extra Shorts (owner 22 Nov: 10M Shorts views for YPP before January).
Stop-game is our best YouTube Short (12.7K vs 1-3K for the rest), so 2 extra a day go to YouTube only, at 10:00 and
15:00 BDT, with famous stars (people search their names). Instagram/Facebook volume stays as planned (6 a day).
"""
import datetime as dt, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "ytextra"
HOURS = (10, 12, 15)  # 24 Nov stats: YouTube-only stop game = our best Short (avg 13K, best 32K)
QUOTA = 20  # uploads cost ~100 units since Dec 2025; 10+ a day worked


def post_due(now):
    from fmm import poster, slots, motion, youtube
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    today = now.strftime("%Y-%m-%d")
    done_today = sum(1 for e in log if e.get("type") == "yt_stopgame" and e.get("at", "")[:10] == today)
    due = sum(1 for h in HOURS if now.hour >= h)
    if done_today >= due or now.hour >= 22:
        return None
    # YouTube API quota: ~6 uploads per Pacific day (resets 14:00 BDT). Only use spare quota, never the main slots'.
    reset = now.replace(hour=14, minute=0, second=0, microsecond=0)
    if now < reset:
        reset -= dt.timedelta(days=1)
    used = sum(1 for e in log if e.get("youtube") and e.get("at", "") >= reset.strftime("%Y-%m-%d %H:%M:%S"))
    mains_left = sum(1 for h in (17, 19, 22, 31, 37) if reset + dt.timedelta(hours=h - 14) > now)  # 17 19 22 07 13
    if used + mains_left + 1 > QUOTA:
        print(f"youtube extra skipped: quota ({used} used, {mains_left} main Shorts still to come)")
        return None
    fresh, db, _ = slots.latest_players()
    pool = sorted(fresh.values(), key=lambda x: -(x.get("ovr") or 0))
    target, kind_ = slots.stop_target(list(db.values()) + pool)  # owner 26 Nov: new 122-124 cards first, then famous (shared with 22:00)
    others = [c["card"] for c in pool if c.get("card") and c["name"] != target["name"]][:14] or [target["card"]]
    name = f"{target['ovr']} {slots.SAY.get(target['name'], target['name']).upper()}"
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    reel = {"id": "slot", "outro": False, "voice": "stopgame",
            "cover": {"subject": target["card"], "text": "CAN YOU\nSTOP ON HIM?", "sub": name, "color": "gold"},
            "scenes": [{"scene": "stopgame", "target": name, "target_card": target["card"], "cards": others}]}
    media = motion.render_reel(reel, OUT)
    say = slots.SAY.get(target["name"], target["name"])
    caption = (f"Can you stop on {say} {target['ovr']}? 🤔\n\nPause on him and comment how many tries it took 👇\n\n"
               "#FCMobile #FIFAMobile #EAFC #Shorts #FMM")
    vid = youtube.upload(media, caption)[0]
    try:
        youtube.add_to_playlist(vid, "stopgame")
    except Exception as ex:
        print("playlist skipped:", str(ex)[:100])
    poster.log({"kind": "reel", "file": str(media), "type": "yt_stopgame", "youtube": vid,
                "stop": kind_, "stop_id": str(target["id"]), "stop_name": f"{target['ovr']} {target['name']}"})
    return vid
