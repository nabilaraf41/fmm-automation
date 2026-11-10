"""Reply to the 2 best comments on each recent post (Instagram + Facebook). Never more than 2 per post.

Best = most likes, then the most substantive text. Skips our own comments, emoji-only / 1-word comments and
anything already replied to. Replies are short, in FMM's voice, varied, and go through the humanizer.
Runs in the 2-hourly job: python -m fmm.replies
"""
import json, random, re, time
from pathlib import Path

from fmm import poster
from fmm.captions import polish

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "content" / "replies.json"
PER_POST = 2
IG_REPLIES = True  # token has instagram_manage_comments (checked 10 Nov 2026)
DAYS = 3

QUESTION = ["Good question! {short}", "{short} Hope that helps 🙌", "{short} Let us know how it goes!"]
THANKS = ["Thanks a lot! More coming every day 🔥", "Appreciate it! Glad you liked it 🙌",
          "Thank you! Stay tuned, more cards and codes daily ⚡", "Thanks bro! 🔥"]
OPINION = ["Fair take! What would you pick instead?", "Interesting pick 👀 Who's in your starting XI?",
           "Respect the opinion! We'll keep testing and update you.", "Could be! Drop your squad, we're curious 👇"]
CODE_Q = "Redeem it at redeem.fcm.ea.com before it expires ⏳"
PACK_Q = "No guarantee, it's just what we're testing 🙏 Try the same time daily and tell us!"


def clean(t):
    return re.sub(r"\s+", " ", t or "").strip()


SPAM = re.compile(r"(join|tournament|dm me|check (my|our)|promo|giveaway|follow (me|back)|http|www\.|\.com|whatsapp|telegram|t\.me)", re.I)


def worth_replying(text):
    if SPAM.search(text):  # promo/bot comments never get a reply (it would boost them under our post)
        return False
    words = re.findall(r"[A-Za-zঀ-৿]{2,}", text)  # Latin or Bangla words
    return len(words) >= 2


def reply_for(text, rnd):
    t = text.lower()
    if "?" in t or re.search(r"\b(how|where|when|what|which|kivabe|kothay)\b", t):
        if "code" in t or "redeem" in t:
            short = CODE_Q
        elif "pack" in t or "trick" in t:
            short = PACK_Q
        else:
            short = "Check our latest posts, we cover it there."
        return rnd.choice(QUESTION).format(short=short)
    if re.search(r"\b(thanks|thank|nice|great|love|best|good|awesome|op|fire)\b", t):
        return rnd.choice(THANKS)
    return rnd.choice(OPINION)


def ig_targets(media_id, me):
    j = poster.call("GET", f"{media_id}/comments", params={"fields": "id,text,like_count,username,replies{username}", "limit": 50})
    out = []
    for c in j.get("data", []):
        if c.get("username") == me or any(r.get("username") == me for r in c.get("replies", {}).get("data", [])):
            continue
        out.append((c.get("like_count", 0), len(clean(c.get("text"))), c["id"], clean(c.get("text"))))
    return out


def fb_targets(obj_id):
    j = poster.call("GET", f"{obj_id}/comments", params={"fields": "id,message,like_count,from,comments{from}", "limit": 50})
    out = []
    for c in j.get("data", []):
        if (c.get("from") or {}).get("id") == poster.PAGE:
            continue
        if any((r.get("from") or {}).get("id") == poster.PAGE for r in c.get("comments", {}).get("data", [])):
            continue
        out.append((c.get("like_count", 0), len(clean(c.get("message"))), c["id"], clean(c.get("message"))))
    return out


def run():
    st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"replied": {}, "per_post": {}}
    log = json.loads((ROOT / "content" / "posted.json").read_text(encoding="utf-8"))
    since = time.strftime("%Y-%m-%d", time.localtime(time.time() - DAYS * 86400))
    me = poster.call("GET", poster.IG, params={"fields": "username"})["username"]
    rnd = random.Random()
    sent = 0
    for e in log:
        if e.get("at", "") < since:
            continue
        for platform, obj, targets, send in (
            ("instagram", None if not IG_REPLIES else e.get("instagram"), lambda o: ig_targets(o, me),
             lambda cid, msg: poster.call("POST", f"{cid}/replies", data={"message": msg})),
            ("facebook", e.get("facebook"), fb_targets,
             lambda cid, msg: poster.call("POST", f"{cid}/comments", data={"message": msg}))):
            if not obj:
                continue
            key = f"{platform}:{obj}"
            left = PER_POST - st["per_post"].get(key, 0)
            if left <= 0:
                continue
            try:
                cands = [c for c in targets(obj) if c[2] not in st["replied"] and worth_replying(c[3])]
            except Exception as ex:
                print(f"{platform} comments skipped:", str(ex)[:120]); continue
            for likes, _, cid, text in sorted(cands, reverse=True)[:left]:
                msg = polish(reply_for(text, rnd)).split("\n")[0]
                try:
                    send(cid, msg)
                except Exception as ex:
                    print(f"{platform} reply failed:", str(ex)[:120]); continue
                st["replied"][cid] = msg
                st["per_post"][key] = st["per_post"].get(key, 0) + 1
                sent += 1
                print(f"replied on {platform}: '{text[:50]}' -> '{msg}'")
                time.sleep(rnd.uniform(4, 10))  # human-like spacing, never a burst
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"replies sent: {sent}")


if __name__ == "__main__":
    r = random.Random(1)
    assert "redeem" in reply_for("where do i use the code?", r).lower()
    assert not worth_replying("🔥🔥") and worth_replying("nice card bro")
    run()
