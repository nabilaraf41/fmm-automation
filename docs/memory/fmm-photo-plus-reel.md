---
name: fmm-photo-plus-reel
description: Never post a picture alone — every photo goes with its Reel on FB + IG + YouTube Shorts (owner rule)
metadata:
  node_type: memory
  type: feedback
  originSessionId: b2f6976c-4048-4597-b0d1-56da525790d0
  modified: 2026-11-05T04:50:59.119Z
---

Every photo post must go out together with its Reel (FB, IG and YouTube Shorts). Never a photo alone.
**Why:** 5 Nov 2026 a manual test posted only the photo (slots.yml post job had no ffmpeg, Reel was skipped);
owner: "never post any picture alone, pic + reels always".
**How to apply:** poster.post() now builds the Reel before posting the photo and raises if it can't, so nothing
posts. Every workflow that posts needs ffmpeg. slots.yml has a "reel" mode to post only the Reel of the latest build.
Links: [[fmm-review-photo-always]] [[fmm-no-pc-posting]]
