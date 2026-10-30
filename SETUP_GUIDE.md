# FMM Automation — Connection Setup Guide ($0)

Do these in order. Never paste passwords or tokens into chat — save tokens only in the `.env` file
(Step 5) or GitHub Secrets.

---

## Step 1 — Instagram → Business account (5 min)
1. Instagram app → Profile → ☰ → **Settings → Account type and tools → Switch to professional account → Business**.
2. Category: *Gaming Video Creator* / *Digital creator*.
3. **Link to Facebook Page:** Settings → *Accounts Center* → *Accounts* → add the **FC Mobile Mania (FMM)** Page.
4. Check in Meta Business Suite → Settings → *Business assets*: both the Page and @fc_fmm show up.

## Step 2 — Meta Developer App (FB Page + Instagram) (20 min)
1. Go to **developers.facebook.com** → log in with the account that is admin of the FMM Page → *Get Started* (verify as developer).
2. **My Apps → Create App** → name `FMM Poster` → use case **"Other"** → type **Business** → link your business portfolio.
3. In the app dashboard, add products: **Facebook Login for Business** and **Instagram (API setup with Facebook login)**.
4. Leave the app in **Development mode**. It only posts to *your own* Page/IG, so no App Review is needed.
5. Open **Tools → Graph API Explorer**:
   - Select your app → *User Token* → add permissions:
     `pages_show_list, pages_read_engagement, pages_manage_posts, pages_manage_engagement, read_insights, instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_insights, business_management`
   - Click **Generate Access Token** → approve for the FMM Page + @fc_fmm.
6. Open **Tools → Access Token Debugger** → paste the token → **Extend Access Token** (makes it 60-day).
7. Back in Graph API Explorer, with the extended token, run: `me/accounts`
   → copy the FMM Page `id` and its `access_token` (a **Page token from a long-lived user token never expires**).
8. Run: `<PAGE_ID>?fields=instagram_business_account` → copy the Instagram account `id`.
9. Note the **App ID** and **App Secret** (App settings → Basic).

You now have: `META_PAGE_ID`, `META_PAGE_TOKEN`, `IG_USER_ID`, `META_APP_ID`, `META_APP_SECRET`.

## Step 3 — Google Cloud (YouTube + Drive + Sheets) (20 min)
1. **console.cloud.google.com** → log in with the Google account that owns @FC_FMM → **New Project** → `FMM Automation`. No billing/card needed.
2. **APIs & Services → Library** → enable: **YouTube Data API v3**, **Google Drive API**, **Google Sheets API**.
3. **OAuth consent screen** → *External* → app name `FMM Automation`, your email → add yourself as **Test user**.
   Then click **Publish app → In production** (stays unverified — fine for personal use; stops tokens expiring every 7 days).
4. **Credentials → Create credentials → OAuth client ID → Desktop app** → download JSON → save as
   `E:\Claude\FMM\secrets\google_client.json`.
5. ⚠️ **YouTube rule:** uploads from an unaudited API project are forced to **Private**. Fix (free):
   submit the **YouTube API Services audit form** (search "YouTube API Services - Audit and Quota Extension Form"),
   describe it as "personal channel auto-upload of my own Shorts". Approval takes ~1–3 weeks.
   Until approved, the script uploads Shorts as private and you flip them public in YouTube Studio (10 sec each),
   **or** you use YouTube Studio's own scheduler.
6. Free quota: 10,000 units/day ≈ **6 uploads/day** — plenty.

## Step 4 — Free media hosting for Instagram (10 min)
Instagram's API needs each image at a public URL. Free option:
1. Create a free **GitHub** account → new **public** repo `fmm-media` → Settings → **Pages** → deploy from `main`.
2. Posts get published there automatically (only finished posts — nothing private).
3. Create a **Fine-grained token** (Settings → Developer settings) with *Contents: read/write* on `fmm-media` only.

## Step 5 — Save tokens locally
Create `E:\Claude\FMM\.env` yourself (Notepad) with:
```
META_APP_ID=
META_APP_SECRET=
META_PAGE_ID=
META_PAGE_TOKEN=
IG_USER_ID=
GITHUB_TOKEN=
GITHUB_MEDIA_REPO=yourname/fmm-media
```
Then tell Claude "tokens are saved" — the scripts read them from this file, Claude does not need to see them.

## Step 6 — Run schedule
- **Option A ($0, PC on):** Windows Task Scheduler runs the poster 3×/day.
- **Option B ($0, PC off):** GitHub Actions in a *private* repo, tokens in GitHub Secrets (2,000 free min/month).

---

## Weekly routine (you, ~45 min)
1. Ask Claude: **"make next week's FMM content"** → you get posts JSON, captions, hashtags, Flow prompts.
2. Make AI images/clips in Google Flow → drop into Drive `FMM/Queue` (optional — text posts work without them).
3. Done. Daily: share Page post into your 2 FB Groups by hand (1 min). Meta does not allow automating groups.

## Ban-safety rules baked into the scripts
- Official APIs only; max 3 FB + 2 IG + 2 YT posts/day; random 5–20 min jitter on post times.
- Different caption per platform; AI-label flag set when Flow media is used.
- No group posting, no auto-follow/like/DM.
