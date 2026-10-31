"""Google Drive inbox for your own gameplay videos.

Put landscape videos (goal clips or full matches) in a Drive folder named "FMM Clips". Each build takes the
next unused highlight (up to 3 per full match, 1 per short clip) and turns it into a vertical Reel.
File-name hints set the title: "skill" -> INSANE SKILL!!, "save" -> WHAT A SAVE!!, "free kick" -> FREE KICK GOAL!!

    python -m fmm.inbox          -> list inbox videos and what's left to post
"""
import io, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "content" / "clips_state.json"
CACHE = ROOT / "output" / "inbox"
FOLDER = "FMM Clips"
FOLDER_ID = "1vNTd0SHdx9RnC4tuvKIQL26Z7WgKWD_E"  # your clips folder (used before the name lookup)
TITLES = [("free kick", "FREE KICK GOAL!!"), ("freekick", "FREE KICK GOAL!!"), ("skill", "INSANE SKILL!!"),
          ("save", "WHAT A SAVE!!"), ("bicycle", "BICYCLE KICK!!"), ("header", "WHAT A HEADER!!"),
          ("long", "LONG SHOT GOAL!!"), ("comeback", "CRAZY COMEBACK!!")]


def drive():
    from googleapiclient.discovery import build
    from fmm import youtube
    return build("drive", "v3", credentials=youtube.creds(), cache_discovery=False)


def state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"files": {}}


def videos(d):
    fid = FOLDER_ID
    if not fid:
        q = f"name = '{FOLDER}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        folders = d.files().list(q=q, fields="files(id)").execute().get("files", [])
        if not folders:
            return []
        fid = folders[0]["id"]
    q = f"'{fid}' in parents and mimeType contains 'video/' and trashed = false"
    return d.files().list(q=q, orderBy="createdTime", fields="files(id,name,size,createdTime)",
                          pageSize=100).execute().get("files", [])


def scorer_card(file_name):
    """Find the player named in the file name (e.g. 'kane free kick.mp4') among confirmed cards -> card path.
    Picks the highest-OVR confirmed card of that player; builds the image if needed."""
    import re, unicodedata
    from fmm import renderz, slots
    norm = lambda s: unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    fname = norm(Path(file_name).stem)
    db = json.loads(renderz.DB.read_text(encoding="utf-8"))["players"] if renderz.DB.exists() else {}
    ok = slots.confirmed_only({str(k): v for k, v in db.items()})
    hits = []
    for p in ok.values():
        n = norm(p.get("name"))
        parts = [n] + ([n.split()[-1]] if len(n.split()) > 1 else [])
        if any(len(x) >= 3 and re.search(rf"\b{re.escape(x)}\b", fname) for x in parts):
            hits.append(p)
    if not hits:
        return None
    best = max(hits, key=lambda p: ((p.get("ovr") or 0), len(p.get("name") or "")))
    path = renderz.CARDS / f"{best['id']}.png"
    if path.exists():
        return str(path)
    try:
        from fmm import fmf
        fresh = {p["id"]: p for p in fmf.latest()}
        return slots.ensure_card(best, fresh)
    except Exception:
        return None


def download(f):
    from googleapiclient.http import MediaIoBaseDownload
    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / f"{f['id']}{Path(f['name']).suffix or '.mp4'}"
    if not local.exists():
        with open(local, "wb") as out:
            dl = MediaIoBaseDownload(out, drive().files().get_media(fileId=f["id"]), chunksize=32 * 1024 * 1024)
            done = False
            while not done:
                _, done = dl.next_chunk()
    return local


def pack_video():
    """Newest pack-opening video ('pack ….mp4') not posted yet; if all are used, the least recently used one."""
    st = state()
    packs = [f for f in videos(drive()) if f["name"].lower().startswith("pack")]
    if not packs:
        return None
    used = st.setdefault("packs", {})
    new = [f for f in packs if f["id"] not in used]
    f = new[-1] if new else min(packs, key=lambda f: used.get(f["id"], ""))
    return f, download(f)


def mark_pack(f):
    import datetime as dt
    st = state()
    st.setdefault("packs", {})[f["id"]] = dt.datetime.now().isoformat(timespec="minutes")
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def post_long():
    """One full video a day to YouTube as a normal (long) video, for watch hours toward monetization.
    Drive files named 'long …' (e.g. 'long full match vs real madrid.mp4'), oldest first, each posted once."""
    import datetime as dt
    st = state()
    done = st.setdefault("long", {})
    today = dt.date.today().isoformat()
    if today in done.values():
        return None
    todo = [f for f in videos(drive()) if f["name"].lower().startswith("long") and f["id"] not in done]
    if not todo:
        return None
    f = todo[0]
    name = Path(f["name"]).stem[4:].strip(" -_").title() or "Full Match"
    nl = chr(10)
    caption = (f"{name} | FC Mobile Full Gameplay 🔥{nl}{nl}Full FC Mobile gameplay from FC Mobile Mania (FMM).{nl}"
               f"Watch till the end and tell us your rating 👇{nl}{nl}Subscribe for daily FC Mobile content 🔔{nl}{nl}"
               "#FCMobile #FCMobile26 #EASportsFCMobile #Gameplay #FMM")
    from fmm import youtube
    vid = youtube.upload(download(f), caption, short=False)[0]
    done[f["id"]] = today
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    return vid


def meme_clip():
    """Download (once) a random meme clip from the Drive folder (files named 'meme ...') -> local path or None."""
    import random
    from googleapiclient.http import MediaIoBaseDownload
    d = drive()
    memes = [f for f in videos(d) if f["name"].lower().startswith("meme")]
    if not memes:
        return None
    f = random.choice(memes)
    CACHE.mkdir(parents=True, exist_ok=True)
    local = CACHE / f"meme_{f['id']}{Path(f['name']).suffix or '.mp4'}"
    if not local.exists():
        with open(local, "wb") as out:
            dl = MediaIoBaseDownload(out, d.files().get_media(fileId=f["id"]), chunksize=32 * 1024 * 1024)
            done = False
            while not done:
                _, done = dl.next_chunk()
    return local


def title_for(name):
    n = name.lower()
    return next((t for k, t in TITLES if k in n), "WHAT A GOAL!!")


def next_clip():
    """Make the next Reel from the inbox -> (mp4_path, title, file_name) or None."""
    from googleapiclient.http import MediaIoBaseDownload
    from fmm import clips
    d = drive()
    st = state()
    for f in videos(d):
        if f["name"].lower().startswith(("meme", "pack", "long")):  # memes -> EA Logic Reels, packs -> Thu/Sun pack Reels
            continue
        rec = st["files"].setdefault(f["id"], {"name": f["name"], "used": 0, "total": None})
        if rec["total"] is not None and rec["used"] >= rec["total"]:
            continue
        CACHE.mkdir(parents=True, exist_ok=True)
        local = CACHE / f"{f['id']}{Path(f['name']).suffix or '.mp4'}"
        if not local.exists():
            with open(local, "wb") as out:
                dl = MediaIoBaseDownload(out, d.files().get_media(fileId=f["id"]), chunksize=32 * 1024 * 1024)
                done = False
                while not done:
                    _, done = dl.next_chunk()
        rec["total"] = len(clips.peaks(local))
        if rec["used"] >= rec["total"]:
            continue
        title = title_for(f["name"])
        card = scorer_card(f["name"])
        print("scorer card:", card or "none found in file name")
        mp4 = clips.make(local, title, rec["used"], sub="FOLLOW FOR DAILY FC MOBILE", card=card)
        rec["used"] += 1
        STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
        return mp4, title, f["name"]
    return None


if __name__ == "__main__":
    d = drive()
    st = state()
    vs = videos(d)
    print(f'"{FOLDER}": {len(vs)} videos')
    for f in vs:
        r = st["files"].get(f["id"], {})
        print(f"  {f['name']}  used {r.get('used', 0)}/{r.get('total', '?')}")
