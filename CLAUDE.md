# FMM (FC Mobile Mania) — automation handbook

Owner's social accounts: FB Page "FC Mobile Mania - FMM" (id 705738725948110), IG @fc_fmm (17841473352545444),
YouTube "FC Mobile Mania - FMM". Owner is in Bangladesh (BDT = UTC+6), zero budget, non-technical:
give click-by-click steps and copy-paste commands.

## Rules
- **Cross-check before posting anything** (cards, events, players): a 2nd source must confirm it
  (RenderZ or creators' YouTube titles). Enforced by `slots.confirmed_only`; manual list in
  `content/featured.json` → `confirmed_programs`, `hold_programs` (TOTW27 held until confirmed).
- Never commit tokens. Secrets live in `.env`, `secrets/` (gitignored) and GitHub Secrets.
- Creating repos / uploading may be blocked for Claude: give the owner the command to run.
- Reviews are original FMM wording from stats (FMM Player Review Standard); never copy RenderZ/forum text.
- No engagement bait ("tag a friend", "react to vote"); FB Groups stay manual.

## Where it runs
Private repo `nabilaraf41/fmm-automation`, GitHub Actions (PC can be off):
- `.github/workflows/codes.yml` ("FMM hourly") — every 2 hours at :05: `fmm.run_cloud` → posts any slot due in the last
  5 h and not yet done (`featured.json` → `done_slots`; GitHub cron can be late or skip runs), then new-player drops
  (`fmm.newplayers`) and redeem codes (`fmm.codes`). Slots (BDT): 07:00 Reel (US), 13:00 photo, 19:00 photo (Indonesia peak), 21:00 Reel (BD/India peak).
- `.github/workflows/slots.yml` — manual runs only (build / post a slot by hand).
- Secrets: META_PAGE_TOKEN (never expires), META_PAGE_ID, IG_USER_ID, META_APP_ID/SECRET, YOUTUBE_TOKEN_JSON
  (Google OAuth: youtube.upload, youtube.readonly, drive.readonly; app "FMM Automation" published).

## Slot logic (`fmm/slots.py`)
1. Owner's clips first: Google Drive folder id 1vNTd0SHdx9RnC4tuvKIQL26Z7WgKWD_E (`fmm.inbox` → `fmm.clips`:
   loud-moment highlights, vertical layout, punch-in, slow-mo replay, sfx, cover). ~1 Reel per 75 s of footage.
   The scorer's card comes from the file name (e.g. "kane free kick.mp4" → Kane's best confirmed card) and is shown
   in the Reel and as the cover subject (`inbox.scorer_card`).
   Pack openings: Drive videos named "pack …" → Thu + Sun 21:00 Reel (`slots.build_pack`, caption from
   content/pack_caption.txt); newest unused first, else the least recently used. "meme …" videos feed EA-logic Reels.
   "long …" videos → one normal (long) YouTube + Facebook upload a day for watch hours (`inbox.post_long`).
2. Reel slots: review Reel of next unreviewed confirmed card from this week (trending on YouTube first, then OVR).
3. Photo slots rotate: review, 1v1 stats comparison, pick-one (3 cards + reactions), guess, top-4 stats table,
   budget XI, rate, hidden gem, "is the event worth it", meme. Design references: assets/references/.
- Weekly growth loop (`fmm.growth`, Mondays): scores last week's posts (YT views, IG views/likes/comments, FB
  likes/comments) → content/weekly_report.md; sets featured.json boost (extra turns) / drop (skipped) for photo formats.
- One-off overrides: `featured.json` → `force` (e.g. {"0700": "countdown"}).
- Card sources: RenderZ (blocked from cloud, 403) → fcmobileforum `/players` (`fmm.fmf`, card = bg + render).

## Modules
brand.py (photo templates, FMM colours/fonts) · motion.py (animated Reels + sfx + whip transitions) ·
thumb.py (MrBeast-style covers, set as IG cover / FB + YT thumbnail) · poster.py (FB/IG Graph API, YT) ·
youtube.py · trends.py (YouTube trends + program confirmation) · review.py · rewards.py (code reward icons) ·
renderz.py / fmf.py (card data) · clean.py (rembg, needs `.venv312`) · sfx.py (generated sound effects).

## Open items
- YouTube API audit not submitted/approved yet (uploads currently publish public; watch for lock to private).
- Content strategy: CONTENT_STRATEGY.md · setup steps: SETUP_GUIDE.md.
