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
    q = f"name = '{FOLDER}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    folders = d.files().list(q=q, fields="files(id)").execute().get("files", [])
    if not folders:
        return []
    q = f"'{folders[0]['id']}' in parents and mimeType contains 'video/' and trashed = false"
    return d.files().list(q=q, orderBy="createdTime", fields="files(id,name,size,createdTime)",
                          pageSize=100).execute().get("files", [])


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
        mp4 = clips.make(local, title, rec["used"], sub="FOLLOW FOR DAILY FC MOBILE")
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
