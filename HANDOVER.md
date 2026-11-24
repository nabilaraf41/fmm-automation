# Handover (updated 25 Nov 2026)

Any agent (Claude, Codex, Antigravity): handbook = CLAUDE.md, this file = status. Memory notes: docs/memory/.

## Status 25 Nov
- Daily (BDT): 07:00 Top 10 (IG carousel + 7 s Reel, star names in title), 13:00 weekly special
  (Mon/Thu Back Four, Tue Front Three, Wed/Sat Best Attack, Fri Shard Guide, Sun Budget XI), 17:00 Choose 1
  (Sun: Legends vs Legends), 19:00 Top 10, 21:00 stop game (Thu/Sun pack opening). Owner's stop-game order is
  slots.STOP_GAME_STARS (famous + top-paying-country heroes, then 3 new cards).
- ONE extra a day 10:00-21:59 (run_cloud.extra_ok): Tue/Wed EA teaser "Guess who's coming" (fmm.teaser),
  Thu/Fri new players' shard cost (fmm.shardcost), else leak / goal Reel / concept special / ATB meme (alternating).
  YouTube-only stop-game Shorts 3/day 10, 12, 15 (fmm.ytextra) = our best YouTube Shorts.
- Codes: FC Mobile Forum alone is enough (owner 22 Nov; RZPROBE was a real Vietnam code — never auto-delete posts).
- IG collabs: fmm/collabs.py + content/collaborators.json (keep, prefer, only, not_visible; addon_fcm and
  fc_bangladesh_402 are "User not visible"). YouTube: no collab API; descriptions @mention partners; real invites
  only by hand in YouTube Studio ("YT" shortcut, needs the owner signed in to the browser).
- Gameplay Reels: only scoreboard-verified goals (tools/goal_detect_study.py) or owner-named short clips, max 1/day
  (fmm/goalreel.py JOBS, made on the PC, posted by the cloud). Loudness auto-clips are off (slots.GAMEPLAY_REELS).

## Open items
- Owner asked for a subscriber "goal" badge on every post: two designs shown 25 Nov (fixed 1,499 vs real count);
  waiting for his pick. Not built.
- Drive has 11 new full-match recordings (16 Nov). Download them one at a time (a 1 GB file hit MemoryError with a
  64 MB chunk in one Python process), then run goal detection and add verified goals to goalreel.JOBS.
- 2 owner clips queued: g5 R9 vs 6 defenders, g6 Pacho own goal (assets/goal_reels).
- Facebook Reels get ~0 plays (published fine): owner should check Page quality in Meta Business Suite.


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
- Stop-game Reel (slots ctype "stopgame", motion.sc_stopgame): "Can you stop on <name>?" cards flash 9 s loop.
  The player named in the hook is the card viewers can pause on. The cover uses the same card.
  Order: this week's confirmed new cards first (state featured.json stop_new), then a rotation of confirmed stars.
  Posts Fri + Sat 21:00 when new cards exist, and any 21:00 Reel
  slot that would otherwise skip. Owner removed phone notifications: never add alerts.
- Recap videos (fmm/recap.py) Sunday + month-end from 20:00 BDT. Comment 🙌 line in every caption + first comment.
- Research 11 Nov (docs/CREATOR_PLAYBOOK.md end): gameplay comedy/bugs/GK fails go most viral -> owner to upload
  'meme ….mp4' clips; cheap-players 7 s loops; stop-game format built from that study.
- IG collabs (12 Nov): content/collaborators.json. newcomer_fm only accepts PHOTOS of Top 10 + new-card reviews ->
  "prefer" puts him on photo:statrank + photo:newcard; everywhere else all partners (incl. delete_fc) rotate 3 per post. Never on
  stop-game Reels (poster._NO_COLLAB). Check acceptance: GET /{ig-media-id}/collaborators (invite_status).
- Sound (12 Nov, followers complained "no sound"): every Reel now has ATB's VOICE with a line that fits the post
  (atb.VOICE: post type -> voiced clips; transcripts of all 73 voiced clips in content/atb_voice.json), music quietly
  under it. Photo Reels: reel.make_reel(kind=ctype); animated Reels: motion -> atb.box(voice=...). Transcribe new clips
  with .venv312 + faster-whisper (decode audio with ffmpeg first; av version mismatch).
- 15 Nov owner rules: NO Reels from H2H videos (highlight + clip Reels removed; full long video to YT/FB stays).
  Stop-game Reel keeps the CORRECT name (named player = card shown). Collab + fcthunder_ea.
  Pending: "NEW ICON & HEROES" (Diogo Jota 124 ST, David Silva 124 CAM, Nasri 123 LM, Van der Vaart 123 CM,
  Kerimoglu 122 CDM, Defoe 122 ST, Hyypia 122 CB, Baines 122 LB, Pedersen 122 LM, Kolo Toure 122 CB) seen on FC Mobile
  Forum only -> post as leak (fmm.leaks, PC) once a 2nd source confirms; on release newplayers posts the drop grid itself.
- Collabs 16 Nov: + hamza.dzn_ (big creator, agreed) in rotation. Top acceptors goat_editv, theeliteelastico, eafc_jacobek08 get double turns (listed twice in
  "rotate"). Low (<25%): aftab.fc, fc_highlightss, newcomer_fm, fcthunder_ea got a reminder DM from the owner.
  ON/AFTER 23 Nov: re-run the acceptance check (GET /{ig-media}/collaborators) and REMOVE anyone still under 20%
  (tell the owner who). newcomer_fm keeps "prefer" (Top 10 + new-card photos) only if he accepts those.
- Goal Reels (16 Nov, owner approved): fmm/goalreel.py builds on the PC from goals the OWNER confirms (JOBS: source,
  parts [(start, end, label)], title, card); ~10-11 s per goal (study: multi-goal 25-35 s best); recordings are often
  silent -> music + impact per goal + ATB "goal" voice. Cloud posts one a day (goalreel.post_due). Ronaldinho hat-trick
  queued 16 Nov. Replay recordings (post-match replays) have no scoreboard: ask owner which replay is whose goal.
- Auto-save hook in .claude/settings.json (local, gitignored): exports chat + memory after every reply.
- Collabs v2 (16 Nov): fmm/collabs.py picks up to 5 per post (poster tries 5, then 3, then none): 3 best-fit partners
  for that exact post type (acceptance per type in content/collab_stats.json, refreshed weekly in run_cloud) + 2
  rotating spots for everyone. "always"/"prefer" in collaborators.json still override.
- YPP target 31 Dec 2026 (owner "a must"): see CREATOR_PLAYBOOK "YouTube monetization goal". Track Shorts views/90d
  + watch hours weekly. Long-video queue now newest upload first (Kaka H2H long 16 Nov).
- Bug sweep 16 Nov (60 run logs): (1) duplicate guard in poster.post (same type + same file within 45 min = skip;
  13 Nov stop-game posted twice); (2) slots.post refuses builds older than 3 h (never repost leftovers); (3) dm.py
  stops retrying archived/deleted chats (44 errors per run); (4) Top 10/XI fallbacks fixed earlier (card stats cache,
  XI reuses lineup). Shard-price API 403s from the cloud: XI reuses the saved lineup. Collabs + elite_fc.02, dfx_eafc.
- YouTube re-login needed (16 Nov): scope youtube.force-ssl added (fmm/youtube.py SCOPES) for comment replies
  (replies.py yt_targets/yt_send) + auto playlists (youtube.add_to_playlist, ids in content/yt_playlists.json,
  "FC Mobile <topic> <year>"). Until the owner runs `python -m fmm.youtube login` and the secret is updated
  (`gh secret set YOUTUBE_TOKEN_JSON -R nabilaraf41/fmm-automation < secrets/youtube_token.json`), both just log "skipped".
  Owner won't show his face: use Google Flow ATB clips for face-to-camera tips (credits reset ~26-29 Nov).
- Custom cards (16 Nov): fmm/cardmaker.py card(bg_page, ovr, pos, name, player=URL|local png) -> stamped "FMM CONCEPT".
  Special posts queue = assets/goal_reels/special_N_*.png|mp4 + .txt (goalreel.post_due, max 2/day, N order):
  CR7 x Portugal 2003-2026, 130 Ronaldo tribute, 130 ATB mascot, follower-card call-out, 125 Hamza. Follower cards:
  owner collects names/photos from comments+DMs weekly -> make with cardmaker (photo cutout via fmm.clean) -> queue.
