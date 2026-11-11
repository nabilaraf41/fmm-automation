# FMM (FC Mobile Mania) — automation handbook

New chat? Read HANDOVER.md first (status, open items, what was fixed and must not be reintroduced).
Full text of every earlier chat (owner's words, decisions, fixes) is in docs/history/*.md (PC only, gitignored, secrets removed).
Whenever the owner refers to something earlier, or you're unsure what was decided, Grep docs/history before answering or asking.
At the end of a long chat: `python -m fmm.export_chat` (same format, secrets removed). All switch-chat prompts: SWITCH_CHAT.md.

Owner's social accounts: FB Page "FC Mobile Mania - FMM" (id 705738725948110), IG @fc_fmm (17841473352545444),
YouTube "FC Mobile Mania - FMM". Owner is in Bangladesh (BDT = UTC+6), zero budget, non-technical:
give click-by-click steps and copy-paste commands.

## Rules
- Follow docs/CREATOR_PLAYBOOK.md for every post; update it from the Monday growth report.
- Follow docs/DESIGN_PLAYBOOK.md for every image, Reel frame and cover (layouts, fonts, ATB safe zone).
- **Cross-check before posting anything** (cards, events, players): a 2nd source must confirm it
  (RenderZ or creators' YouTube titles). Enforced by `slots.confirmed_only`; manual list in
  `content/featured.json` → `confirmed_programs`, `hold_programs` (TOTW27 held until confirmed).
- State (content/*.json) is saved with `python -m fmm.savestate "msg"` (merges with concurrent cloud saves);
  never plain-push state files from the PC while a cloud run may be saving.
- Never commit tokens. Secrets live in `.env`, `secrets/` (gitignored) and GitHub Secrets.
- Creating repos / uploading may be blocked for Claude: give the owner the command to run.
- Reviews are original FMM wording from stats (FMM Player Review Standard); never copy RenderZ/forum text.
- No engagement bait ("tag a friend", "react to vote"); FB Groups stay manual.

## Where it runs
Private repo `nabilaraf41/fmm-automation`, GitHub Actions (PC can be off):
- `.github/workflows/codes.yml` ("FMM hourly") — every 2 hours at :05: `fmm.run_cloud` → posts any slot due in the last
  5 h and not yet done (`featured.json` → `done_slots`; GitHub cron can be late or skip runs), then new-player drops
  (`fmm.newplayers`) and redeem codes (`fmm.codes`). Slots (BDT): 07:00 Top 10 (photo + Reel), 13:00 photo, 19:00 photo (Indonesia peak), 21:00 Reel (BD/India peak).
- Backup trigger: Google Apps Script (owner's Google account, GOOGLE_TRIGGER.gs) dispatches codes.yml every hour,
  because GitHub skips scheduled runs on busy days. Uses a fine-grained PAT (Actions write) stored in Script properties.
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
   "long …" / full "h2h" videos → one long YouTube + Facebook upload a day at 18:00 BDT, 1440p, ATB facecam, plus a
  goal-highlight Reel on FB + IG + YT (`inbox.post_long`, goal times in content/long_goals.json).
2. Reel slots: review Reel of next unreviewed confirmed card from this week (trending on YouTube first, then OVR).
3. Photo slots rotate: review, 1v1 stats comparison, pick-one (3 cards + reactions), guess, top-4 stats table,
   budget XI, rate, hidden gem, "is the event worth it", meme. Design references: assets/references/.
- ATB Meme (`fmm.atbmeme`): owner says what goes on the right; add {top, bottom, label} to content/atb_meme.json
  queue (cards as "Name OVR POS", confirmed only). Posts one a day at 15:00 BDT (photo + Reel). ATB images: assets/atb_meme.
- Leaks / predictions (`fmm.leaks`): cards not out yet are made on the PC like FC Mobile Forum (old RenderZ render on
  the new event's bg); queue in content/leaks.json (2+ sources), `python -m fmm.leaks make`, commit; cloud posts 11:00 BDT.
- Weekly growth loop (`fmm.growth`, Mondays): scores last week's posts (YT views, IG views/likes/comments, FB
  likes/comments) → content/weekly_report.md; sets featured.json boost (extra turns) / drop (skipped) for photo formats.
- Instagram collabs: content/collaborators.json {"usernames": [...]} (owner-agreed partners), up to 3 invited per post, rotating daily; bad name -> posts without collab.
- One-off overrides: `featured.json` → `force` keyed by date-slot (e.g. {"2026-11-05-0700": "countdown"}); undated keys are ignored.
- Card sources: RenderZ (blocked from cloud, 403) → fcmobileforum `/players` (`fmm.fmf`, card = bg + render).

## Modules
brand.py (photo templates, FMM colours/fonts) · motion.py (animated Reels + sfx + whip transitions) ·
thumb.py (MrBeast-style covers, set as IG cover / FB + YT thumbnail) · poster.py (FB/IG Graph API, YT) ·
youtube.py · trends.py (YouTube trends + program confirmation) · review.py · rewards.py (code reward icons) ·
renderz.py / fmf.py (card data) · clean.py (rembg, needs `.venv312`) · sfx.py (generated sound effects).

## Open items
- YouTube API audit not submitted/approved yet (uploads currently publish public; watch for lock to private).
- Content strategy: CONTENT_STRATEGY.md · setup steps: SETUP_GUIDE.md.

## Memory backup
Copies of the chat's memory notes live in docs/memory/. On a new PC, copy them to ~/.claude/projects/<project>/memory/.
