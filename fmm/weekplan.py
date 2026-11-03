"""The coming 7 days, slot by slot, for the owner to check (Google Doc via GOOGLE_TRIGGER.gs, and content/week_plan.md).

Made on Thursdays after the new cards land. A plan, not a promise: each post is still built ~1 h before its slot,
so new cards, codes, Drive clips and confirmed events can change it.
    python -m fmm.weekplan      -> write content/week_plan.md now
"""
import copy, datetime as dt, types
from pathlib import Path

from fmm import slots

OUT = Path(__file__).resolve().parent.parent / "content" / "week_plan.md"
XI = {"attack": "Budget XI part 1/3: attack", "defence": "Budget XI part 2/3: defence",
      "midfield": "Budget XI part 3/3: midfield", "xi": "Budget XI: starting XI", "all": "Budget XI: all 4 (swipe post)"}


def plan(start=None):
    start = start or dt.date.today()
    fresh, db, _ = slots.latest_players()
    st = copy.deepcopy(slots.load_state())  # dry run: nothing is saved
    lines = [f"# FMM plan: {start:%a %d %b} to {start + dt.timedelta(days=6):%a %d %b %Y}", "",
             "Times are Bangladesh time. Each post also goes out as a Reel (photos too).", ""]
    real_dt = slots.dt
    try:
        for i in range(7):
            day = start + dt.timedelta(days=i)
            # make slots.pick see this day
            slots.dt = types.SimpleNamespace(
                date=type("D", (dt.date,), {"today": classmethod(lambda c, d=day: d)}),
                datetime=type("T", (dt.datetime,), {"now": classmethod(lambda c, tz=None, d=day: dt.datetime(d.year, d.month, d.day, 12, tzinfo=tz))}),
                timedelta=dt.timedelta, UTC=dt.UTC)
            lines += [f"## {day:%A %d %b}", "", "| Time | Post |", "|---|---|"]
            for slot in sorted(slots.SLOTS):
                slots._SLOT["v"] = slot
                if slot == "2100" and day.weekday() in (3, 6):
                    what = "Pack opening Reel (your newest 'pack ...' video)"
                else:
                    try:
                        ctype, players, _ = slots.pick(slots.SLOTS[slot], fresh, db, st)
                    except Exception as ex:
                        ctype, players = f"(could not plan: {str(ex)[:40]})", []
                    what = describe(ctype, players, st, day)
                    for p in players[:1] if ctype.startswith("review") else []:
                        st["featured"] += [str(p["id"]), f"{p['name']}|{p['ovr']}|{p['pos']}"]
                lines.append(f"| {slot[:2]}:{slot[2:]} | {what} |")
            lines.append("")
    finally:
        slots.dt = real_dt
    lines += ["Extras any day: new redeem codes, new-player drop (Thursday), your Drive clips (they go first).", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    return "\n".join(lines)


def describe(ctype, players, st, day):
    p = players[0] if players else {}
    if ctype in ("review_reel", "review_post"):
        return f"Review {'Reel' if ctype == 'review_reel' else 'photo'}: {p.get('ovr')} {p.get('pos')} {p.get('name')}"
    if ctype == "xi":
        f = str(st.get("force", {}).get(f"{day.isoformat()}-1300") or "")
        step = f.split(":", 1)[1] if ":" in f else {3: "attack", 4: "defence", 5: "midfield", 6: "xi"}.get(day.weekday(), "all")
        return XI.get(step, "Budget XI")
    if ctype == "statrank":
        s, pos = slots.series_today()
        return f"Top 10 {pos.replace('ALL ', 'all of ')} by {slots.STAT_NAME[s]}"
    if ctype == "choose":
        g = [["CB", "LB", "RB"], ["ST", "LW", "RW"], ["CM", "CAM", "CDM"]][day.toordinal() % 3]
        return f"Choose 1: four 122+ {g[(day.toordinal() // 3) % 3]} cards"
    if ctype == "versus":
        return "Stats battle: " + " vs ".join(f"{x.get('ovr')} {x.get('name')}" for x in players[:2])
    return {"countdown": "Countdown Reel: this week's best new cards", "tierlist": "Tier list Reel: this week's cards",
            "rank10": "Top 10 ranking", "pick3": "Pick one (3 cards)", "guess": "Guess the player", "compare4": "Top 4 stats table",
            "rate": "Rate the card", "gem": "Hidden gem", "worth": "Is the event worth it?", "meme": "Meme"}.get(ctype, ctype)


if __name__ == "__main__":
    print(plan())
