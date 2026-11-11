"""Post photos and Reels to the FMM Facebook Page and Instagram via the official Graph API.

No extra hosting needed: Instagram photos are fetched from a temporary *unpublished* Facebook photo,
and Reels upload directly (resumable upload).

    python -m fmm.poster check                         -> token + quota check, posts nothing
    python -m fmm.poster photo <png> <caption.txt> [fb|ig|both]
    python -m fmm.poster reel  <mp4> <caption.txt> [fb|ig|both]
    python -m fmm.poster queue <folder>                -> posts every png/mp4 with a matching .txt caption
"""
import json, os, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
G = "https://graph.facebook.com/v26.0"
LOG = ROOT / "content" / "posted.json"  # committed, so cloud runs remember what was posted


def env():
    """Local: .env file. Cloud (GitHub Actions): environment variables from repository secrets."""
    e = {k: os.environ[k] for k in ("META_PAGE_TOKEN", "META_PAGE_ID", "IG_USER_ID") if os.environ.get(k)}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                e.setdefault(k.strip(), v.strip())
    return e


E = env()
TOKEN, PAGE, IG = E["META_PAGE_TOKEN"], E["META_PAGE_ID"], E["IG_USER_ID"]


def call(method, path, **kw):
    kw.setdefault("params", {})["access_token"] = TOKEN
    r = requests.request(method, f"{G}/{path}", timeout=300, **kw)
    j = r.json()
    if "error" in j:
        raise RuntimeError(f"{path}: {j['error'].get('message')}")
    return j


def log(entry):
    data = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    data.append({"at": time.strftime("%Y-%m-%d %H:%M:%S"), **entry})
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# ---------- Facebook ----------
def fb_video(path, caption):
    """Normal (long) Facebook video, uploaded in chunks (big files fail in one request).
    Eligible for in-stream ads when 3+ minutes."""
    url = f"https://graph-video.facebook.com/v26.0/{PAGE}/videos"
    size = os.path.getsize(path)
    j = requests.post(url, data={"access_token": TOKEN, "upload_phase": "start", "file_size": size}, timeout=120).json()
    if "error" in j:
        raise RuntimeError(f"FB video start: {j['error'].get('message')}")
    sid, start, end = j["upload_session_id"], int(j["start_offset"]), int(j["end_offset"])
    with open(path, "rb") as f:
        while start < end:
            f.seek(start)
            chunk = f.read(end - start)
            r = requests.post(url, data={"access_token": TOKEN, "upload_phase": "transfer", "upload_session_id": sid,
                                         "start_offset": start}, files={"video_file_chunk": chunk}, timeout=600).json()
            if "error" in r:
                raise RuntimeError(f"FB video transfer: {r['error'].get('message')}")
            start, end = int(r["start_offset"]), int(r["end_offset"])
    r = requests.post(url, data={"access_token": TOKEN, "upload_phase": "finish", "upload_session_id": sid,
                                 "description": caption}, timeout=120).json()
    if "error" in r or not r.get("success"):
        raise RuntimeError(f"FB video finish: {r}")
    return j.get("video_id") or sid


def fb_photo(path, caption, published=True):
    with open(path, "rb") as f:
        j = call("POST", f"{PAGE}/photos", data={"caption": caption, "published": str(published).lower(),
                                               **({} if published else {"temporary": "true"})},
                 files={"source": f})
    return j["id"]


def cover_for(media):
    """Reel cover made by fmm.thumb: <name>_cover.jpg next to <name>.mp4."""
    c = Path(media).with_name(Path(media).stem + "_cover.jpg")
    return c if c.exists() else None


def fb_thumbnail(video_id, cover, tries=8):
    """Right after upload the video "does not exist" while FB processes it: retry for ~4 min."""
    for i in range(tries):
        try:
            with open(cover, "rb") as f:
                call("POST", f"{video_id}/thumbnails", data={"is_preferred": "true"}, files={"source": f})
            return True
        except Exception as ex:
            if i == tries - 1:
                print("fb thumbnail skipped:", str(ex)[:120])
            else:
                time.sleep(30)
    return False


def fb_reel(path, caption):
    start = call("POST", f"{PAGE}/video_reels", data={"upload_phase": "start"})
    vid = start["video_id"]
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r = requests.post(start["upload_url"], data=f, timeout=600,
                          headers={"Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(size)})
    if not r.ok or not r.json().get("success"):
        raise RuntimeError(f"FB reel upload failed: {r.text[:300]}")
    call("POST", f"{PAGE}/video_reels", data={"upload_phase": "finish", "video_id": vid,
                                              "video_state": "PUBLISHED", "description": caption})
    if cover_for(path):
        fb_thumbnail(vid, cover_for(path))
    return vid


# ---------- Instagram ----------
def public_url_for(path):
    """Host the image as a temporary unpublished FB photo and return its CDN URL (Instagram fetches from it)."""
    pid = fb_photo(path, "", published=False)
    return call("GET", pid, params={"fields": "images"})["images"][0]["source"]


def ig_wait(cid, tries=60):
    for _ in range(tries):
        st = call("GET", cid, params={"fields": "status_code,status"})
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"IG processing failed: {st}")
        time.sleep(5)
    raise RuntimeError("IG processing timed out")


def ig_publish(cid, tries=5):
    """IG sometimes says "Media ID is not available" right after FINISHED: wait and retry (seen 7 Nov)."""
    for i in range(tries):
        try:
            return call("POST", f"{IG}/media_publish", data={"creation_id": cid})["id"]
        except Exception as ex:
            if i == tries - 1 or "not available" not in str(ex) and "not ready" not in str(ex).lower():
                raise
            time.sleep(20)


COLLAB = ROOT / "content" / "collaborators.json"  # {"usernames": ["name1", ...]} owner's agreed collab partners


def collab_data():
    """Instagram collab invite, max 3 per post: "always" names on every post, "rotate" names take turns (daily)
    for the spots left; {} when none. File: {"always": [...], "rotate": [...]} (old {"usernames": [...]} = rotate)."""
    try:
        j = json.loads(COLLAB.read_text(encoding="utf-8"))
    except Exception:
        return {}
    clean = lambda xs: [n.lstrip("@") for n in xs if n]
    always, rot = clean(j.get("always", []))[:3], clean(j.get("rotate", j.get("usernames", [])))
    k = int(time.time() // 86400) % len(rot) if rot else 0
    names = always + (rot[k:] + rot[:k])[:3 - len(always)]
    return {"collaborators": json.dumps(names)} if names else {}


def ig_container(data):
    """Create a media container with the collab invite; a bad/ineligible username never blocks the post."""
    extra = collab_data()
    if extra:
        try:
            return call("POST", f"{IG}/media", data={**data, **extra})
        except Exception as ex:
            print("collab invite skipped:", str(ex)[:150])
    return call("POST", f"{IG}/media", data=data)


def ig_photo(path, caption):
    cid = ig_container({"image_url": public_url_for(path), "caption": caption})["id"]
    ig_wait(cid)
    return ig_publish(cid)


def ig_carousel(paths, caption):
    kids = []
    for p in paths:
        cid = call("POST", f"{IG}/media", data={"image_url": public_url_for(p), "is_carousel_item": "true"})["id"]
        ig_wait(cid)
        kids.append(cid)
    cid = ig_container({"media_type": "CAROUSEL", "children": ",".join(kids), "caption": caption})["id"]
    ig_wait(cid)
    return ig_publish(cid)


def fb_carousel(paths, caption):
    """One Facebook post with several photos (uploaded unpublished, then attached)."""
    ids = [fb_photo(p, "", published=False) for p in paths]
    data = {"message": caption, **{f"attached_media[{i}]": json.dumps({"media_fbid": x}) for i, x in enumerate(ids)}}
    return call("POST", f"{PAGE}/feed", data=data)["id"]


def post_carousel(paths, caption, ctype=None):
    """Swipe post on Facebook + Instagram; each platform on its own, logged once any succeeds."""
    from fmm.captions import polish
    caption = polish(caption)
    done, errors = {}, {}
    for name, fn in (("facebook", fb_carousel), ("instagram", ig_carousel)):
        try:
            done[name] = fn([str(p) for p in paths], caption)
        except Exception as ex:
            errors[name] = str(ex)[:200]
            print(f"{name} failed:", errors[name])
    if not done:
        raise RuntimeError(f"all platforms failed: {errors}")
    log({"kind": "carousel", "file": str(paths[0]), **({"type": ctype} if ctype else {}), **done})
    return done


def ig_reel(path, caption, share_to_feed=True, trial=False):
    data = {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
            "share_to_feed": str(share_to_feed).lower()}
    if trial:  # Trial Reel: non-followers only; MANUAL so it never lands in the feed next to the main Reel
        data["trial_params"] = json.dumps({"graduation_strategy": "MANUAL"})
    if cover_for(path):
        data["cover_url"] = public_url_for(cover_for(path))
    j = call("POST", f"{IG}/media", data=data) if trial else ig_container(data)  # trial Reels: no collab
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r = requests.post(j["uri"], data=f, timeout=600,
                          headers={"Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(size)})
    if not r.ok:
        raise RuntimeError(f"IG reel upload failed: {r.text[:300]}")
    ig_wait(j["id"])
    return ig_publish(j["id"])


# ---------- high level ----------
# owner rule (10 Nov 2026): every post carries "DAY N/365 · <series>" (N = days that format has been posted)
SERIES = {"xi": "BEST CHEAP XI", "review_reel": "CARD REVIEW", "review_post": "CARD REVIEW", "statrank": "TOP 10 BY STAT",
          "rank10": "TOP 10", "choose": "CHOOSE 1", "pack": "PACK OPENING", "versus": "1V1 STATS", "pick3": "PICK ONE",
          "goat": "GOAT DEBATE", "atb_meme": "ATB MEME", "leak": "LEAKS", "guess": "GUESS THE PLAYER",
          "rate": "RATE IT", "gem": "HIDDEN GEM", "worth": "IS IT WORTH IT", "meme": "EA LOGIC", "clip": "MY GOALS",
          "long": "H2H FULL MATCH", "codes": "REDEEM CODES"}


def day_label(ctype):
    """'DAY 3/365 · BEST CHEAP XI' or None for types without a series."""
    if not ctype or ctype not in SERIES:
        return None
    today = time.strftime("%Y-%m-%d", time.gmtime(time.time() + 6 * 3600))  # BDT
    data = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    days = {e["at"][:10] for e in data if e.get("type") == ctype and e.get("at", "")[:10] < today}
    return f"DAY {len(days) + 1}/365 · {SERIES[ctype]}"


def _pill(label, side):
    from PIL import Image, ImageDraw
    from fmm.brand import title_font
    f = title_font(max(28, side // 17))
    tw = int(f.getlength(label)); th = f.size
    img = Image.new("RGBA", (tw + th * 2, int(th * 1.7)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=img.height // 2, fill=(255, 215, 0, 245),
                        outline=(0, 0, 0, 255), width=4)
    d.text((img.width // 2, img.height // 2), label, font=f, fill=(0, 0, 0, 255), anchor="mm")
    return img


def stamp(media, label):
    """Copy of media with the day pill top-centre -> new path (original untouched, so retries never double-stamp)."""
    from PIL import Image
    src = Path(media)
    if src.suffix.lower() in (".png", ".jpg", ".jpeg"):
        im = Image.open(src).convert("RGBA")
        pill = _pill(label, min(im.size))
        im.alpha_composite(pill, ((im.width - pill.width) // 2, int(im.height * 0.02)))
        out = src.with_name(src.stem + "_day" + src.suffix)
        im.convert("RGB").save(out, quality=95)
        return str(out)
    import subprocess
    w = int(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.split()[0].split(",")[0])
    png = src.with_name(src.stem + "_daypill.png")
    _pill(label, w).save(png)
    out = src.with_name(src.stem + "_day.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-i", str(png), "-filter_complex",
                    "overlay=(W-w)/2:H*0.02", "-c:a", "copy", "-crf", "18", str(out)], check=True)  # top edge, above the ATB face
    cover = cover_for(src)
    if cover:  # keep the cover pairing (cover_for looks next to the mp4)
        import shutil
        shutil.copy(cover, out.with_name(out.stem + Path(cover).name[len(src.stem):]))
    return str(out)


# owner (10 Nov): every post asks for 🙌 in caption + first comment; fmm.dm DMs the codes page to whoever comments it
CTA = "📩 Comment 🙌 and I'll DM you every working FC Mobile code"


def with_cta(caption):
    if "comment 🙌" in caption.lower():
        return caption
    parts = caption.rstrip().split("\n\n")
    if len(parts) > 1 and parts[-1].lstrip().startswith("#"):  # keep hashtags last
        return "\n\n".join(parts[:-1] + [CTA, parts[-1]])
    return caption.rstrip() + "\n\n" + CTA


def cta_comment(done):
    """Same line as the first comment under the new post (Instagram + Facebook). Never blocks the post."""
    for platform, edge in (("instagram", "comments"), ("facebook", "comments")):
        mid = done.get(platform)
        if not mid or not isinstance(mid, str):
            continue
        try:
            call("POST", f"{mid}/{edge}", data={"message": CTA})
        except Exception as ex:
            print(f"{platform} cta comment skipped:", str(ex)[:120])


def post(kind, media, caption, where="both", ctype=None, reel=True, extra=None, _stamp=True):
    """Post to each platform independently. One platform failing never re-posts the others:
    the result is logged as soon as any platform succeeds; it raises only if all of them failed."""
    media = str(media)
    label = day_label(ctype) if _stamp else None
    if label:
        try:
            media = stamp(media, label)
        except Exception as ex:  # a missing pill never blocks the post
            print("day label skipped:", str(ex)[:120])
    from fmm.captions import polish
    caption = with_cta(polish(caption))  # humanized, hook-first, max 5 hashtags; + the 🙌 -> DM line
    pair = None
    if kind == "photo" and where == "both" and reel:  # owner rule: never a photo alone; make its Reel first
        from fmm import reel as reelmod
        pair = reelmod.make_reel(media, seconds=10)  # raises (nothing posted) if the Reel can't be made
    if kind == "reel" and media.endswith(".mp4"):  # every Reel: gold progress bar (once per file)
        try:
            from fmm import motion
            motion.progress_bar(media)
        except Exception as ex:
            print("progress bar skipped:", str(ex)[:120])
    done, errors = {}, {}
    steps = []
    if where in ("fb", "both"):
        steps.append(("facebook", lambda: (fb_photo if kind == "photo" else fb_reel)(media, caption)))
    if where in ("ig", "both"):
        steps.append(("instagram", lambda: (ig_photo if kind == "photo" else ig_reel)(media, caption)))
    if kind == "reel" and where == "both":  # Reels also go to YouTube Shorts
        def yt():
            from fmm import youtube
            return youtube.upload(media, caption.replace("\n\n" + CTA, ""))[0]  # no DMs on YouTube
        steps.append(("youtube", yt))
    for attempt in range(2):  # owner rule: every post on all platforms; a failed one gets a 2nd try
        for name, fn in steps:
            if name in done:
                continue
            try:
                done[name] = fn()
                errors.pop(name, None)
            except Exception as ex:
                errors[name] = str(ex)[:200]
                print(f"{name} failed (try {attempt + 1}):", errors[name])
        if not errors or attempt:
            break
        time.sleep(60)
    if not done:
        raise RuntimeError(f"all platforms failed: {errors}")
    log({"kind": kind, "file": media, **({"type": ctype} if ctype else {}), **(extra or {}), **done})
    cta_comment(done)
    if pair:  # the photo's Reel on Facebook, Instagram and YouTube Shorts
        # not the same text twice in a row on the Page (FB treats it like spam): Reel gets the hook + hashtags only
        parts = [p for p in caption.split("\n\n") if p.strip()]
        short = parts[0] + ("\n\n" + parts[-1] if len(parts) > 1 and "#" in parts[-1] else "")
        done["reel"] = post("reel", pair, short if short != caption else "🎬 " + caption, where, ctype, _stamp=False)
        done["reel_file"] = str(pair)  # lets slots run an Instagram Trial Reel hook test on the same video
    return done


def caption_for(media: Path):
    """code_X.png / code_X_reel.mp4 -> code_X.txt"""
    for cand in (media.with_suffix(".txt"), media.with_name(media.stem.replace("_reel", "") + ".txt")):
        if cand.exists():
            return cand.read_text(encoding="utf-8")
    return None


def posted_files():
    # compare by file name so Windows and cloud paths match
    return {Path(e["file"].replace("\\", "/")).name for e in json.loads(LOG.read_text(encoding="utf-8"))} \
        if LOG.exists() else set()


def run_queue(folder, where="both", gap=90):
    items = sorted(Path(folder).glob("*.png")) + sorted(Path(folder).glob("*.mp4"))  # covers are .jpg, never posted alone
    for m in items:
        cap = caption_for(m)
        if m.name in posted_files() or cap is None:  # re-read: posting a photo also posts its _reel.mp4 (was posted twice)
            continue
        kind = "reel" if m.suffix == ".mp4" else "photo"
        print("posting", kind, m.name, "->", post(kind, m, cap, where))
        time.sleep(gap)  # space posts out; never burst


def check():
    page = call("GET", PAGE, params={"fields": "name,fan_count"})
    ig = call("GET", IG, params={"fields": "username,followers_count"})
    q = call("GET", f"{IG}/content_publishing_limit", params={"fields": "quota_usage,config"})["data"][0]
    print(f"Facebook: {page['name']} ({page['fan_count']} followers)")
    print(f"Instagram: @{ig['username']} ({ig['followers_count']} followers), "
          f"posts used today {q['quota_usage']}/{q['config']['quota_total']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "check":
        check()
    elif a[0] in ("photo", "reel"):
        print(post(a[0], a[1], Path(a[2]).read_text(encoding="utf-8"), a[3] if len(a) > 3 else "both"))
    elif a[0] == "queue":
        run_queue(a[1], a[2] if len(a) > 2 else "both")
