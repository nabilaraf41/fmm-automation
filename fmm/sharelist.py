"""Daily FB-group share list (owner, 11 Nov): groups bring ~90% of Facebook views, but only a person can post there.
After 21:30 BDT: today's 2 best posts (by Instagram views so far) -> phone alert with the Facebook link + a caption.
"""
import json, time
from pathlib import Path
from fmm import notify, poster

STATE = Path(__file__).resolve().parent.parent / "content" / "sharelist.json"


def pick(log, today):
    from fmm import growth
    rows = []
    for e in log:
        if e.get("at", "")[:10] != today or not e.get("facebook") or "trial" in str(e.get("type")):
            continue
        try:
            rows.append((growth.metrics(e).get("ig_views", 0), e))
        except Exception:
            rows.append((0, e))
    rows.sort(key=lambda r: -r[0])
    return [e for _, e in rows[:2]]


def link(e):
    return f"https://www.facebook.com/reel/{e['facebook']}" if e.get("kind") == "reel" else f"https://www.facebook.com/{e['facebook']}"


def run():
    bdt = time.gmtime(time.time() + 6 * 3600)
    today = time.strftime("%Y-%m-%d", bdt)
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    if bdt.tm_hour * 60 + bdt.tm_min < 21 * 60 + 30 or st.get(today):
        return None
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    # the log stores local (BDT on the cloud runner) time
    best = pick(log, today)
    if not best:
        return None
    msg = "\n\n".join(f"{i}. {link(e)}\nCaption: Agree with this? 👇 (FC Mobile Mania)"
                      for i, e in enumerate(best, 1))
    notify.send("📤 Share these 2 in FB groups", msg + "\n\nTap the link → Share → Group. 2 min 🙌", tags="outbox_tray",
                click=link(best[0]))
    st[today] = [e["facebook"] for e in best]
    STATE.write_text(json.dumps(st, indent=1), encoding="utf-8")
    return st[today]


if __name__ == "__main__":
    print(run())
