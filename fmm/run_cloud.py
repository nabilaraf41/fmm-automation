"""The 2-hourly cloud run (.github/workflows/codes.yml, every 2 hours at :05).

1. Due slot: if a slot time (07:00/13:00/19:00/21:00 BDT) has passed in the last 5 hours and wasn't posted,
   build it and post it now. GitHub cron can be late or skip runs, so every slot is caught up by the next run.
2. New-player drops and redeem codes (extra posts).
Safe to run any number of times: featured.json "done_slots", codes_state.json and posted.json stop repeats.
"""
import datetime as dt
import json
import time
from fmm import codes, poster, slots

BDT = dt.timezone(dt.timedelta(hours=6))
CATCH_UP = dt.timedelta(hours=5)  # 2-hourly runs: still covered if one run is skipped
EARLY = dt.timedelta(minutes=75)  # owner: post exactly on time, so start early, build, then wait for the slot


def due_slot(now, done):
    """Latest slot whose time passed within CATCH_UP and isn't in done -> (key, slot) or None."""
    for back in range(2):  # today and yesterday (00:30 belongs to the next calendar day)
        day = (now - dt.timedelta(days=back)).date()
        for slot in sorted(slots.SLOTS, reverse=True):
            t = dt.datetime.combine(day, dt.time(int(slot[:2]), int(slot[2:])), BDT)
            key = f"{day}-{slot}"
            if t - EARLY <= now < t + CATCH_UP and key not in done:
                return key, slot
    return None


def run_slot(now):
    st = slots.load_state()
    done = st.setdefault("done_slots", {})
    due = due_slot(now, done)
    if not due:
        print("no slot due")
        return
    key, slot = due
    tries = st.setdefault("slot_tries", {}).get(key, 0)
    if tries >= 2:  # failed twice: give up on this one rather than risk a half-posted duplicate
        done[key] = "gave up"
        slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
        return
    st["slot_tries"][key] = tries + 1
    slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    print("posting slot", key)
    if slots.build(slot) == "skip":  # weak Reel slot: nothing posts, marked done so later runs don't retry it
        st = slots.load_state()
        st.setdefault("done_slots", {})[key] = "skipped (nothing strong)"
        st.get("slot_tries", {}).pop(key, None)
        slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
        return
    t = dt.datetime.combine(dt.date.fromisoformat(key[:10]), dt.time(int(slot[:2]), int(slot[2:])), BDT)
    wait = (t - dt.datetime.now(BDT)).total_seconds()
    if wait > 0:  # built early: hold it until the exact slot time
        print(f"built, waiting {wait / 60:.0f} min for {slot}")
        time.sleep(wait)
    slots.post()
    st = slots.load_state()  # build() updated the state file
    st.setdefault("done_slots", {})[key] = now.isoformat(timespec="minutes")
    st["done_slots"] = dict(list(st["done_slots"].items())[-40:])
    st.get("slot_tries", {}).pop(key, None)
    slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    # self-check of the catch-up rule
    _n = dt.datetime(2026, 11, 1, 7, 40, tzinfo=BDT)
    assert due_slot(_n, {}) == ("2026-11-01-0700", "0700")
    assert due_slot(_n, {"2026-11-01-0700": 1}) is None
    assert due_slot(dt.datetime(2026, 11, 1, 1, 30, tzinfo=BDT), {}) == ("2026-10-31-2100", "2100")
    assert due_slot(dt.datetime(2026, 11, 1, 12, 30, tzinfo=BDT), {}) == ("2026-11-01-1300", "1300")  # early start
    assert due_slot(dt.datetime(2026, 11, 1, 15, 0, tzinfo=BDT), {"2026-11-01-1300": 1}) is None

    now = dt.datetime.now(BDT)
    # long video first: run_slot may wait up to an hour for the next slot, and the job has a 100-minute limit
    try:  # one long YouTube video a day from Drive 'long …' files (watch hours for the Partner Program)
        from fmm import inbox
        v = inbox.post_long()
        if v:
            print("long video uploaded:", v)
    except Exception as ex:
        print("long video skipped:", str(ex)[:150])
    try:
        run_slot(now)
    except Exception as ex:
        print("slot failed (next hourly run retries):", str(ex)[:200])
    try:  # leaks / predictions made on the PC (content/leaks.json): one a day from 11:00 BDT, photo + Reel
        from fmm import leaks
        m = leaks.post_due()
        if m:
            print("leak posted:", m)
    except Exception as ex:
        print("leak skipped:", str(ex)[:150])
    try:  # owner's "ATB Meme" (content/atb_meme.json queue): one a day from 15:00 BDT, photo + Reel
        from fmm import atbmeme
        m = atbmeme.post_due()
        if m:
            print("atb meme posted:", m)
    except Exception as ex:
        print("atb meme skipped:", str(ex)[:150])
    try:  # reply to the 2 best comments per recent post (Instagram + Facebook)
        from fmm import replies
        replies.run()
    except Exception as ex:
        print("replies skipped:", str(ex)[:150])
    try:  # Tuesday night: weekly growth report + more of what works
        from fmm import growth
        growth.run()
    except Exception as ex:
        print("growth report skipped:", str(ex)[:150])
    try:  # new-player drops (Thursday 07:00 BDT, or any surprise batch) -> extra posts
        from fmm import newplayers
        newplayers.run()
    except Exception as ex:
        print("new-player check skipped:", str(ex)[:150])
    try:  # Thursday afternoon (after the drop): next 7 days' plan -> content/week_plan.md -> owner's Google Doc
        st = slots.load_state()
        if now.weekday() == 3 and now.hour >= 14 and st.get("plan_day") != now.date().isoformat():
            from fmm import weekplan
            weekplan.plan()
            st = slots.load_state()
            st["plan_day"] = now.date().isoformat()
            slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    except Exception as ex:
        print("week plan skipped:", str(ex)[:150])
    codes.run()
    today = codes.QUEUE / dt.date.today().isoformat()
    if today.exists():
        poster.run_queue(today, "both")
    else:
        print("nothing new to post")
