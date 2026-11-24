"""Weekly "GUESS WHO'S COMING?" (owner 24 Nov). Every Tuesday EA posts a teaser of next Thursday's players
(silhouette cards: OVR, position, nation flag). The cloud reads @easfcmobile through the Graph API (business_discovery),
puts the teaser in an FMM frame and posts it Tue/Wed 10:00-21:59 BDT as photo + Reel. Counts as that day's extra post.
"""
import datetime as dt, io, json, re
from pathlib import Path
import requests
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "teaser"
HINT = re.compile(r"this thursday|next week|guess|coming|arriv", re.I)
FLAG = re.compile("[\U0001F1E6-\U0001F1FF]{2}|\U0001F3F4[\U000E0061-\U000E007A]+\U000E007F")


def find(days=4):
    """Newest EA post of the last `days` days that teases upcoming players -> (image bytes, caption) or None."""
    from fmm import poster
    e = poster.env()
    fields = "business_discovery.username(easfcmobile){media.limit(10){caption,media_type,media_url,thumbnail_url,timestamp}}"
    r = requests.get(f"https://graph.facebook.com/v21.0/{e['IG_USER_ID']}",
                     params={"fields": fields, "access_token": poster.TOKEN}, timeout=30).json()
    since = (dt.datetime.now(dt.UTC) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S")
    for m in r.get("business_discovery", {}).get("media", {}).get("data", []):
        cap = m.get("caption") or ""
        url = m.get("thumbnail_url") or m.get("media_url")
        if m.get("timestamp", "") >= since and url and HINT.search(cap) and "choose your side" not in cap.lower():
            return requests.get(url, timeout=30).content, cap
    return None


def render(img_bytes, event, out):
    from fmm import brand
    W, H = 1080, 1350
    img, d, _ = brand.base("event", None, (W, H))
    img = img.convert("RGBA"); d = ImageDraw.Draw(img)
    d.text((W / 2, 200), "GUESS WHO'S", font=brand.font("Anton-Regular.ttf", 110), fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, 315), "COMING?", font=brand.font("Anton-Regular.ttf", 130), fill=(200, 255, 0), anchor="mm")
    if event:
        d.text((W / 2, 415), event.upper(), font=brand.label_font(38), fill=(255, 215, 0), anchor="mm")
    t = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    t = ImageOps.contain(t, (980, 815))
    frame = Image.new("RGBA", (t.width + 16, t.height + 16), (200, 255, 0, 255))
    frame.paste(t, (8, 8))
    img.alpha_composite(frame, ((W - frame.width) // 2, 450))
    d.text((W / 2, H - 45), "DROP YOUR GUESSES  •  SOURCE: EA SPORTS FC MOBILE", font=brand.label_font(24),
           fill=(220, 220, 220), anchor="mm")
    img.convert("RGB").save(out, quality=94)
    return out


def build(found=None):
    found = found or find()
    if not found:
        return None, None
    img_bytes, cap = found
    ev = re.search(r"([A-Z][A-Za-z' ]{2,30}Week \d+)", cap)
    event = ev.group(1).strip() if ev else ""
    flags = " ".join(dict.fromkeys(FLAG.findall(cap)))
    OUT.mkdir(parents=True, exist_ok=True)
    out = render(img_bytes, event, OUT / "teaser.png")
    caption = (f"Guess who's coming{' in ' + event if event else ' next'}? 🤔🔥 {flags}\n\n"
               "EA just teased the next players: OVR, position and nation are in the picture.\n"
               "Drop your guesses below 👇 We'll reveal them on Thursday.\n\n"
               "#FCMobile #FIFAMobile #EAFC #FCMobileLeaks #FMM")
    return out, caption


def post_due(now):
    """Tuesday or Wednesday 10:00-21:59 BDT, once a week."""
    from fmm import poster
    if now.weekday() not in (1, 2) or not 10 <= now.hour < 22:
        return None
    log = json.loads(poster.LOG.read_text(encoding="utf-8")) if poster.LOG.exists() else []
    monday = (now - dt.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    if any(e.get("type") == "teaser" and e.get("at", "") >= monday for e in log):
        return None
    img, cap = build()
    return poster.post("photo", img, cap, "both", "teaser") if img else None
