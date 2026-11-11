# Handover (updated 8 Nov 2026, from chat b2f6976c)

Previous chat transcript (open only if something below is unclear):
`C:\Users\Admin\.claude\projects\E--Claude-FMM\b2f6976c-4048-4597-b0d1-56da525790d0.jsonl`
Handbook = CLAUDE.md. Memory notes (~/.claude/projects/E--Claude-FMM/memory, backup docs/memory/) load automatically.

## Status
- Only the cloud posts (repo nabilaraf41/fmm-automation, codes.yml, 100-min job limit; Google Apps Script dispatches hourly at :32).
- Slots BDT: 07:00 Reel, 13:00 photo (Budget XI Thu–Mon), 17:00 "Choose 1", 19:00 "Top 10 by stat" (31-day series from 3 Nov),
  21:00 Reel (Thu/Sun pack opening). Extras: 11:00 leak/prediction (fmm.leaks), 15:00 ATB Meme (fmm.atbmeme),
  18:00 long video (inbox.post_long: YT + FB 1440p60 with ATB facecam + goal-highlight Reel), codes, new-player drops.
- Every photo goes with its Reel (FB + IG photo, Reel on FB + IG + YT Shorts). YouTube can't take photos (no API).
  The Reel now gets a shorter caption (hook + hashtags) so the FB Page never shows the same text twice in a row.
- ATB (owner) is in every post: badge on photos, clip on top of photo Reels, facecam on long videos. Flow account
  nabilaraf24: all credits spent, reset ~26–29 Nov.

## Added 6–8 Nov
- Long videos: run first in run_cloud (before slot wait); facecam `fps=60` (H2H screen recordings are VFR, r_frame_rate 90000,
  made ffmpeg encode forever); 1440p veryfast; LOOK sharpen/grade on all gameplay. Goal times in content/long_goals.json.
- FB Reel cover: fb_thumbnail retries ~4 min (FB says the video "does not exist" while processing).
- All 3 platforms: ig_publish retries "Media ID is not available"; post() gives every failed platform a 2nd try after 60 s;
  run_queue re-reads posted.json (code Reel was posted twice); match highlight goes to FB + IG + YT.
- ATB Meme: assets/atb_meme/{no,yes}.jpg; queue content/atb_meme.json; first one (Mbappé 120 vs 119) posted 7 Nov.
- Leaks: unreleased cards = old RenderZ render + new event bg (find RenderZ pages in the browser, renderz.app/players?q=Name);
  queue content/leaks.json (2+ sources), `python -m fmm.leaks make` on PC, commit. Week 4 Ballon d'Or prediction queued 8 Nov
  (Owen, Cruyff, Olise, Gabriel; Díaz + Rummenigge left out, single source). Sources: FC Mobile Forum, @MadridistaaFC.
- renderz.js_to_json handles JS short floats (-.8).

## Fixed earlier (don't reintroduce)
- Long videos post at 18:00 BDT so they're indexed before the 20–23h BD/India viewing peak (own data: 21:00 is the best hour).
- Never name a scratch/helper file after a stdlib module: queue.py shadowed Python's `queue` and broke urllib3/requests
  (renamed queuepk.py).
- State is saved only with `python -m fmm.savestate` (merges; can add but not remove keys → use marker values like "redo").
  Commit code before savestate. Local test runs change content/players_db.json + clips_state.json: `git checkout -- content` them.
- Workflows check out `ref: main`. `force` overrides are keyed "YYYY-MM-DD-HHMM".
- Poster posts each platform independently; a slot is done once any platform succeeds.

## Codes page (9 Nov)
- Public repo nabilaraf41/fmm-codes = https://nabilaraf41.github.io/fmm-codes/ (latest 5 codes, copy buttons).
  Updates itself hourly (its own Action reads fcmobileforum; no token). Edit design in that repo's codespage.py.
- Comment 🙌/code -> DM: built in-house (fmm/dm.py, Page /messages private reply), no ManyChat needed. Owner pins the evergreen post.
  Add 'Comment "CODE" ...' to code captions only after ManyChat is live.

## Open items
- FB Page reach ~0 (Reels 0–2 plays vs IG 1.4k–4.5k, 0 reactions). Owner to check Professional dashboard → Page status
  (send screenshot) and share Reels to FB groups/personal profile. Owner wants photo + Reel on FB kept.
- Check that the 11:00 leak post (8 Nov) reached FB + IG + YT; it's the first of its type.
- Owner may delete one copy of the duplicate code Reel (FB 1633325401906458, IG 18029433419920196, YT MA4V7xdGBWM).
- After Flow credits reset: chained 20 s pack reaction; retry 5 hook clips. Idea: music bed for silent long videos.
- Possible: Top 10 series with fully-trained stats / CM by Pace (owner asked if this format posts — it does, 19:00).
- Instagram comment replies ON since 10 Nov (2 per post, spam skipped). YouTube API audit not submitted.

## Added 11 Nov
- Owner doesn't want phone notifications (11 Nov): ntfy alerts + share list were built and removed. Don't re-add.
- FB content monetization: owner already approved and earning.
- Recap long videos (fmm/recap.py): Sunday Top 5 of the week, month-end Best of (top 10), from 20:00 BDT.
- Top 10: "Part N" in title (no '#': polish turns #N into a hashtag), 07:00 Brazil line + #FCMobileBrasil,
  Trial Reel hook tests on Top 10 + Cheap XI (slots.PHOTO_HOOKS). Comment 🙌 -> DM (fmm/dm.py) on all posts except the
  pinned codes post (ManyChat owns that one). Hands-on-head ATB clip deleted (looked bald).
