"""Comment-to-DM bot (our own ManyChat): someone comments the keyword (🙌 or "code") on a keyword post ->
they get a private DM with the codes page, and a short public "Sent you a DM 📩" reply under their comment.

Keyword post = caption has "Comment 🙌" (playbook keyword-DM pattern). Works on Instagram and Facebook through
the Page's /messages endpoint (recipient = comment_id, Meta's "private reply": one per comment, within 7 days).
Also posts the evergreen "Comment 🙌" codes post once from the cloud (owner pins it on IG by hand).
Runs in the hourly cloud job: python -m fmm.dm
"""
import json, re, time
from pathlib import Path

import requests
from fmm import poster

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "content" / "dms.json"
EVERGREEN = ROOT / "assets" / "evergreen" / "codes_comment.png"
LINK = "https://nabilaraf41.github.io/fmm-codes/"
KEY = re.compile(r"🙌|\bcodes?\b", re.I)
ASK = re.compile(r"comment\s*🙌", re.I)
DAYS = 7  # Meta allows a private reply only within 7 days of the comment
MAX_RUN = 60
DM = ("Here you go 🙌\n\nEvery working FC Mobile code, checked every hour (copy in one tap):\n" + LINK +
      "\n\nFollow @fc_fmm so you never miss the next drop 🔔")
PUBLIC = ["Sent you a DM 📩", "Check your DMs 📩", "Sent! Check your inbox 📩", "DM sent 🙌"]


def load():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}


def save(st):
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def get(path, **params):
    r = requests.get(f"https://graph.facebook.com/v21.0/{path}", params={"access_token": poster.TOKEN, **params}, timeout=60)
    return r.json()


def private_reply(comment_id):
    """True = sent (or Meta says it already has one: counts as done)."""
    r = requests.post(f"https://graph.facebook.com/v21.0/{poster.PAGE}/messages", params={"access_token": poster.TOKEN},
                      json={"recipient": {"comment_id": comment_id}, "message": {"text": DM}}, timeout=60)
    if r.ok or "already has a reply" in r.text:
        return True
    print("dm failed:", r.text[:200])
    return False


def keyword_posts(st):
    """(platform, media id) of recent posts whose caption asks for the keyword; captions cached in state."""
    since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - DAYS * 86400))
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    cache = st.setdefault("asks", {})
    out = []
    for e in log:
        if e.get("at", "") < since and e.get("type") != "evergreen":  # the pinned post keeps working forever
            continue
        for platform, field, cap in (("instagram", "instagram", "caption"), ("facebook", "facebook", "message")):
            mid = str(e.get(field) or "")
            if not mid or not re.fullmatch(r"[\d_]+", mid):
                continue
            if mid not in cache:
                cache[mid] = bool(ASK.search(get(mid, fields=cap).get(cap, "") or ""))
            if cache[mid]:
                out.append((platform, mid))
    return out


def comments(platform, mid):
    if platform == "instagram":
        j = get(f"{mid}/comments", fields="id,text,username,timestamp", limit=50)
        return [(c["id"], c.get("text", ""), c.get("username"), c.get("timestamp", "")) for c in j.get("data", [])]
    j = get(f"{mid}/comments", fields="id,message,from,created_time", limit=50)
    return [(c["id"], c.get("message", ""), (c.get("from") or {}).get("id"), c.get("created_time", ""))
            for c in j.get("data", [])]


def post_evergreen(st):
    """One-time: the pinned 'Comment 🙌' codes post (photo + Reel, all platforms)."""
    if st.get("evergreen_posted") or not EVERGREEN.exists():
        return
    cap = EVERGREEN.with_suffix(".txt").read_text(encoding="utf-8")
    poster.post("photo", EVERGREEN, cap, "both", "evergreen")
    st["evergreen_posted"] = time.strftime("%Y-%m-%d")
    print("evergreen codes post published: pin it on Instagram (⋯ -> Pin to profile)")


def run():
    st = load()
    try:
        post_evergreen(st)
    except Exception as ex:
        print("evergreen post skipped:", str(ex)[:150])
    done = st.setdefault("done", {})
    me = {"fc_fmm", "nabilaraf41_bot", poster.PAGE}
    cutoff = time.strftime("%Y-%m-%dT%H:%M", time.gmtime(time.time() - DAYS * 86400))
    sent = 0
    for platform, mid in keyword_posts(st):
        for cid, text, who, ts in comments(platform, mid):
            if cid in done or who in me or ts[:16] < cutoff or not KEY.search(text or ""):
                continue
            if sent >= MAX_RUN:
                break
            if private_reply(cid):
                done[cid] = time.strftime("%Y-%m-%d %H:%M")
                sent += 1
                try:  # public proof under the comment (people see it works and comment too)
                    edge = "replies" if platform == "instagram" else "comments"
                    poster.call("POST", f"{cid}/{edge}", data={"message": PUBLIC[sent % len(PUBLIC)]})
                except Exception as ex:
                    print("public reply skipped:", str(ex)[:100])
            time.sleep(2)
    save(st)
    print(f"dm: {sent} sent")
    return sent


if __name__ == "__main__":
    run()
