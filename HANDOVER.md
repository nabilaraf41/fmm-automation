# Handover from chat "1" (31 Oct – 1 Nov 2026)

Full transcript backup: `C:\Users\Admin\Downloads\session-export-1793493412525.zip` (open only if something below is unclear).
The handbook is CLAUDE.md; memory notes load automatically when the chat is opened in `E:\Claude\FMM`.

## Status (1 Nov 2026, 21:00 BDT)
- Everything posts from the cloud (repo nabilaraf41/fmm-automation). Google Apps Script starts the job every hour.
- Slots BDT: 07:00 Reel, 13:00 photo, 19:00 photo, 21:00 Reel (Thu/Sun 21:00 = pack opening).
- Extras: redeem codes, new-player drops (Thu 07:00), Drive clips ("pack …", "meme …", "long …", player-named goals),
  long videos to YouTube + Facebook, Facebook comment replies (max 2/post), Monday growth report.
- Captions pass through the humanizer (fmm/captions.py). 13 ig-* skills in .claude/skills; voice in ~/.claude/instagram/voice.md.

## Added 1 Nov 2026 (later the same day)
- Every photo post is also posted as a 10 s zoom Reel/Short (`poster.post` -> `reel.make_reel`, 4K source + sharpen).
- RkReddy / top-50 study (memory notes in docs/memory/): clip Reels ~12 s, pack Reels ~15 s around the reveal,
  reaction + number hooks (BROKEN/INSANE only for 9+ ratings), clip captions = file name + ☠️🔥, tags #FCMobile #FIFAMobile #EAFC.
- Stats battle (`slots.next_pair`): same EXACT position only, both cards 122+ OVR, new card vs best card at that
  position (old cards allowed, cross-checked), each pair once. Owner rules — keep them.
- Chat 2 was deleted; this chat ("1") is the only working chat. Full backup zip: Downloads\FMM-BACKUP-2026-11-01.zip.

## Fixed in chat 1 (don't reintroduce)
- State is saved only with `python -m fmm.savestate` (merges; keeps local commits). Never plain-push state files.
- Workflows check out `ref: main`. One-off overrides in featured.json `force` are keyed "YYYY-MM-DD-HHMM".
- The merge save can add but not remove keys/list items: design new state so nothing needs deleting.
- Poster posts each platform independently; a slot is done once any platform succeeds.

## Open items
- Owner to delete duplicate posts from 31 Oct (newer copies of the 13:00 and 21:00 posts, YouTube tU6M6p6bxGw /
  SFY3_2hs9sY, and the second COSTUMEPARTY set incl. YouTube eXmjKlpt4as).
- Instagram comment replies off (IG_REPLIES=False) until the token gets instagram_manage_comments.
- YouTube API audit not submitted. Fine-grained GitHub token for the Google trigger expires 31 Oct 2027.
- Owner records without game audio; asked to enable internal audio. Raw 4 recordings are retired.
- Ideas not built: profile score (ig-profile needs a screenshot), 16:9 cover for every long video exists; facebook
  reel views not scored in growth report.
