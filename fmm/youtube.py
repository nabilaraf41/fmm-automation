"""Upload Shorts to the FC_FMM YouTube channel (YouTube Data API v3).

    python -m fmm.youtube login                       -> one-time browser consent, saves secrets/youtube_token.json
    python -m fmm.youtube check                       -> channel name + subscriber count
    python -m fmm.youtube upload <mp4> <caption.txt> [private|unlisted|public]

Until Google approves the API audit, YouTube forces API uploads to PRIVATE; flip them public in YouTube Studio.
Cloud: set secret YOUTUBE_TOKEN_JSON to the contents of secrets/youtube_token.json.
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLIENT = ROOT / "secrets" / "google_client.json"
TOKEN = ROOT / "secrets" / "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/drive.readonly",  # Drive: read your "FMM Clips" inbox folder
          "https://www.googleapis.com/auth/youtube.force-ssl"]  # 16 Nov: reply to comments + manage playlists


def creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    info = json.loads(os.environ["YOUTUBE_TOKEN_JSON"]) if os.environ.get("YOUTUBE_TOKEN_JSON") else \
        json.loads(TOKEN.read_text(encoding="utf-8"))
    c = Credentials.from_authorized_user_info(info)  # use exactly the scopes this login granted
    if not c.valid:
        c.refresh(Request())
    return c


def service():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds(), cache_discovery=False)


def login():
    from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    c = flow.run_local_server(port=0, prompt="consent", access_type="offline",
                              success_message="FMM YouTube connected. You can close this tab.")
    TOKEN.write_text(c.to_json(), encoding="utf-8")
    print("saved", TOKEN)


def check():
    ch = service().channels().list(part="snippet,statistics", mine=True).execute()["items"][0]
    print(f"YouTube: {ch['snippet']['title']} ({ch['statistics'].get('subscriberCount')} subscribers)")


# owner 16 Nov: every video goes into its playlist (search traffic -> watch hours). Year in the name, updated in January.
PLAYLISTS = {"statrank": "Top 10", "rank10": "Top 10", "xi": "Cheap Players & Best XI", "pack": "Pack Opening",
             "code": "Redeem Codes", "code_reel": "Redeem Codes", "review_reel": "New Players & Reviews",
             "newcard": "New Players & Reviews", "goal_reel": "Goals & Gameplay", "clip": "Goals & Gameplay",
             "long": "Full H2H Matches", "stopgame": "Games & Funny Moments", "choose": "Games & Funny Moments",
             "atb_meme": "Games & Funny Moments", "leak": "Leaks & Predictions", "recap_week": "Best Of",
             "recap_month": "Best Of"}


def add_to_playlist(video_id, ctype):
    """Put the video in 'FC Mobile <topic> <year>' (created on first use). Needs the youtube.force-ssl login."""
    topic = PLAYLISTS.get(ctype or "")
    if not topic or not video_id:
        return None
    import datetime as dt
    title = f"FC Mobile {topic} {dt.date.today().year}"
    cache = ROOT / "content" / "yt_playlists.json"
    ids = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else {}
    yt = service()
    if title not in ids:
        found = [p for p in yt.playlists().list(part="snippet", mine=True, maxResults=50).execute()["items"]
                 if p["snippet"]["title"] == title]
        ids[title] = found[0]["id"] if found else yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": title, "description": f"Every FC Mobile {topic.lower()} video by FC Mobile Mania (FMM)."},
            "status": {"privacyStatus": "public"}}).execute()["id"]
        cache.write_text(json.dumps(ids, indent=1), encoding="utf-8")
    yt.playlistItems().insert(part="snippet", body={"snippet": {
        "playlistId": ids[title], "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
    return title


def title_and_description(caption, short=True):
    """First caption line -> title (max 100 chars, with | FC Mobile), rest -> description."""
    lines = [l for l in caption.strip().splitlines()]
    title = lines[0].strip()
    if "fc mobile" not in title.lower() and len(title) <= 40:  # short reaction titles first; the tag only if room
        title += " | FC Mobile"
    return title[:100], caption.strip() + ("\n\n#Shorts" if short else "")


def latest_long():
    """YouTube id of the newest long video in content/posted.json, or None."""
    import json
    log = Path(__file__).resolve().parent.parent / "content" / "posted.json"
    ids = [e["youtube"] for e in json.loads(log.read_text(encoding="utf-8")) if e.get("kind") == "long" and e.get("youtube")]         if log.exists() else []
    return ids[-1] if ids else None


def upload(path, caption, privacy="public", short=True):
    from googleapiclient.http import MediaFileUpload
    title, desc = title_and_description(caption, short)
    if short and (lv := latest_long()):  # every Short points to the newest full match (watch hours for YPP)
        desc = desc.replace("\n\n#Shorts", f"\n\nFull match: https://youtu.be/{lv}\n\n#Shorts")
    body = {"snippet": {"title": title, "description": desc, "categoryId": "20",  # Gaming
                        "tags": ["FC Mobile", "FC Mobile 26", "EA Sports FC Mobile", "FMM", "FC Mobile Mania"]},
            "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}}
    req = service().videos().insert(part="snippet,status", body=body,
                                    media_body=MediaFileUpload(str(path), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    cover = Path(path).with_name(Path(path).stem + "_cover.jpg")
    if cover.exists():  # custom thumbnail (needs a phone-verified channel)
        try:
            service().thumbnails().set(videoId=resp["id"], media_body=MediaFileUpload(str(cover))).execute()
        except Exception as ex:
            print("yt thumbnail skipped:", str(ex)[:150])
    return resp["id"], resp["status"]["privacyStatus"]


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "login":
        login()
    elif a and a[0] == "upload":
        print(upload(a[1], Path(a[2]).read_text(encoding="utf-8"), a[3] if len(a) > 3 else "public"))
    else:
        check()
