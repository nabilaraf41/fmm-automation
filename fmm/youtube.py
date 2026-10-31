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
          "https://www.googleapis.com/auth/drive.readonly"]  # Drive: read your "FMM Clips" inbox folder


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


def title_and_description(caption, short=True):
    """First caption line -> title (max 100 chars, with | FC Mobile), rest -> description."""
    lines = [l for l in caption.strip().splitlines()]
    title = lines[0].strip()
    if "fc mobile" not in title.lower():
        title += " | FC Mobile"
    return title[:100], caption.strip() + ("\n\n#Shorts" if short else "")


def upload(path, caption, privacy="public", short=True):
    from googleapiclient.http import MediaFileUpload
    title, desc = title_and_description(caption, short)
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
