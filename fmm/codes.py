"""Daily FC Mobile redeem-code watcher.

Reads the active-codes list from fcmobileforum.com/fcmobile-redeem-codes (robots.txt allows it; we only read
code names, rewards and dates — short factual items), then for each NEW code makes a photo post + Reel + captions,
and every day makes one "all active codes" roundup post.

Usage:  python -m fmm.codes            -> output/queue/<date>/...  (state in content/codes_state.json)
        python -m fmm.codes --dry      -> just print what is active / new
"""
import datetime as dt, html, json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "content" / "codes_state.json"
QUEUE = ROOT / "output" / "queue"
URL = "https://fcmobileforum.com/fcmobile-redeem-codes"
UA = "FMM-code-check/1.0 (+https://www.facebook.com/61577183936749)"
REDEEM_SITE = "redeem.fcm.ea.com"


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def parse_active(page):
    """Return [{code, reward, date}] from the 'Active Codes' column only."""
    start = page.find("Active Codes")
    end = page.find("Expired Codes", start)
    if start < 0 or end < 0:
        raise RuntimeError("Page layout changed: could not find Active/Expired sections")
    block = page[start:end]
    out = []
    for box in re.split(r'class="[^"]*codeBox[^"]*"', block)[1:]:
        code = re.search(r"redeemCode=([A-Za-z0-9]+)", box)
        reward = re.search(r'codeReward[^"]*">([^<]+)<', box)
        date = re.search(r'codeDate[^"]*">([^<]+)<', box)
        if code:
            out.append({"code": code.group(1).upper(),
                        "reward": html.unescape(reward.group(1)).strip() if reward else "Free reward",
                        "date": html.unescape(date.group(1)).strip() if date else ""})
    return out


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"seen": {}, "roundups": []}


PINNED = "📩 Comment 🙌 and I'll DM you every working code"  # fmm.dm sends the codes page


def caption_new(c):
    return (f"🎁 NEW FC MOBILE CODE: {c['code']}\n\n"
            f"Reward: {c['reward']}\n"
            f"Redeem now at {REDEEM_SITE} before it expires ⏳\n\n"
            f"👇 Did it work for you? Tell us what you got!\n\n{PINNED}\n\n"
            f"#FCMobile #FCMobile26 #FCMobileCodes #RedeemCode #FMM")


def caption_roundup(active):
    lines = "\n".join(f"✅ {c['code']} — {c['reward']}" for c in active)
    return (f"📋 ALL ACTIVE FC MOBILE CODES ({dt.date.today():%d %b})\n\n{lines}\n\n"
            f"Redeem at {REDEEM_SITE}\n"
            f"🔔 Follow FMM — we post every new code first.\n{PINNED}\n\n"
            f"#FCMobile #FCMobile26 #FCMobileCodes #FreeRewards #FMM")


def pick_card(reward):
    """Reward visual by type (gems, MLS player, draft token, ...): see fmm/rewards.py."""
    from fmm import rewards
    return rewards.pick(reward)


def run(dry=False):
    from fmm import brand, motion  # heavy imports only when rendering
    active = parse_active(fetch())
    state = load_state()
    new = [c for c in active if c["code"] not in state["seen"]]
    print("active:", [c["code"] for c in active], "| new:", [c["code"] for c in new])
    if dry:
        return
    today = dt.date.today().isoformat()
    day_dir = QUEUE / today
    made = []
    for c in new:
        card = pick_card(c["reward"])
        post = {"id": f"code_{c['code']}", "type": "code", "title": "New Code!!", "subtitle": c["reward"],
                "code": c["code"], "reward_image": card}
        made.append(brand.render(post, day_dir))
        from fmm import rewards
        kind = rewards.kind_of(c["reward"])
        headline = {"gems": "FREE GEMS!!", "player": "FREE PLAYER!!", "mls": "FREE PLAYER!!", "draft": "FREE DRAFT!!",
                    "tokens": "FREE FC POINTS!!", "rankup": "FREE RANK UP!!"}.get(kind, "NEW CODE!!")
        reel = {"id": f"code_{c['code']}_reel",
                "cover": {"subject": card, "text": headline, "sub": f"CODE: {c['code']}", "color": "gold", "emoji": "wow"},
                "scenes": [{"scene": "code", "code": c["code"], "card": card, "reward": c["reward"]}]}
        made.append(motion.render_reel(reel, day_dir))
        (day_dir / f"code_{c['code']}.txt").write_text(caption_new(c), encoding="utf-8")
        state["seen"][c["code"]] = {"first_seen": today, **c}
    if active and today not in state["roundups"]:
        post = {"id": "codes_roundup", "type": "codes_list", "codes": active}
        made.append(brand.render(post, day_dir))
        (day_dir / "codes_roundup.txt").write_text(caption_roundup(active), encoding="utf-8")
        state["roundups"].append(today)
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    for m in made:
        print("made", m)


if __name__ == "__main__":
    run(dry="--dry" in sys.argv)
