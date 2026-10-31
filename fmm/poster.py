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


def fb_thumbnail(video_id, cover):
    try:
        with open(cover, "rb") as f:
            call("POST", f"{video_id}/thumbnails", data={"is_preferred": "true"}, files={"source": f})
    except Exception as ex:
        print("fb thumbnail skipped:", str(ex)[:120])


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


def ig_publish(cid):
    return call("POST", f"{IG}/media_publish", data={"creation_id": cid})["id"]


def ig_photo(path, caption):
    cid = call("POST", f"{IG}/media", data={"image_url": public_url_for(path), "caption": caption})["id"]
    ig_wait(cid)
    return ig_publish(cid)


def ig_reel(path, caption, share_to_feed=True):
    data = {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
            "share_to_feed": str(share_to_feed).lower()}
    if cover_for(path):
        data["cover_url"] = public_url_for(cover_for(path))
    j = call("POST", f"{IG}/media", data=data)
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        r = requests.post(j["uri"], data=f, timeout=600,
                          headers={"Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(size)})
    if not r.ok:
        raise RuntimeError(f"IG reel upload failed: {r.text[:300]}")
    ig_wait(j["id"])
    return ig_publish(j["id"])


# ---------- high level ----------
def post(kind, media, caption, where="both", ctype=None):
    media = str(media)
    done = {}
    if where in ("fb", "both"):
        done["facebook"] = (fb_photo if kind == "photo" else fb_reel)(media, caption)
    if where in ("ig", "both"):
        done["instagram"] = (ig_photo if kind == "photo" else ig_reel)(media, caption)
    if kind == "reel" and where == "both":  # Reels also go to YouTube Shorts, when YouTube is connected
        try:
            from fmm import youtube
            done["youtube"] = youtube.upload(media, caption)[0]
        except Exception as ex:  # YouTube problems must never block FB/IG posting
            print("youtube skipped:", str(ex)[:200])
    log({"kind": kind, "file": media, **({"type": ctype} if ctype else {}), **done})
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
    done = posted_files()
    items = sorted(Path(folder).glob("*.png")) + sorted(Path(folder).glob("*.mp4"))  # covers are .jpg, never posted alone
    for m in items:
        cap = caption_for(m)
        if m.name in done or cap is None:
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
