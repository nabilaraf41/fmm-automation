---
name: fmm-atb-host
description: "ATB (owner, \"Araf The Boss\") is the FMM host â€” every post shows him; Flow character + asset rules"
metadata:
  node_type: memory
  type: project
  originSessionId: b2f6976c-4048-4597-b0d1-56da525790d0
  modified: 2026-11-05T03:44:16.853Z
---

Owner = ATB (Araf The Boss), FMM host. Google Flow character "ATB" (voice Charon, deep male) on account
ligadobd@gmail.com, project 2466b431-ac3f-4ed0-91d8-a0a0a21c46a7. Owner has more Google accounts for credits.
Rules from owner (5 Nov 2026):
- Every post shows ATB: photo posts get a small round face badge (fmm/atb.py add_badge, bottom-right, from
  assets/atb_face), photo Reels show an ATB reaction clip on top (assets/atb_clips, fmm/reel.make_reel).
- Looks: bright and fair, about 20% lighter skin than the raw Flow output (fmm/brighten.py), never darker, never more than that.
- Realistic only, nothing that looks AI (no light sweeps across the face, no on-screen text). High energy, deep voice.
- Phone: only the BACK of the phone may face the camera, never the screen (screens show irrelevant junk).
- Never use a clip where he looks bald/almost bald (atb_09_pack_hype deleted).
- Save the highest quality (videos 1080p upscaled, images 4K).
- Full library on PC: E:\Claude\FMM\03-Clips\FMM Clips\{Assets,Images,Rejected} (gitignored); owner uploads to Drive.
- Flow video: 10 credits per 6 s Omni clip; images free (Nano Banana Pro) but rate-limited after ~40 prompts.
Links: [[fmm-user-preferences]] [[fmm-design-references]]

- Reel audio: music low; ATB voice only on clips with generic lines (atb_clips files that keep an audio track). Topic-specific lines = music only.
- New Flow account => first read the week plan (content/week_plan.md) and make reactions that match the scheduled posts/types (review intro, budget XI, choose 1, top 10, pack opening, CR7 vs Messi...).

2026-11-06: Flow account nabilaraf24 (credits reset ~2026-11-26). ATB character there = jersey body + voice "charon".
Flow agent chat costs 12 credits per 8 s Omni 1.1 Flash video; batch prompts work (agent asks to approve the total).
Made: assets/atb_long (12 calm, 4 goal, 4 concede) + 9 pack (n_j*) + 3 review clips = 384 credits; ~516 left.
Browser downloads from Flow land in ~/Downloads (the anchor hook dies on page reload).
2026-11-06 later: all 900 credits spent. +37 clips in ~30 real places (n_p*: 11 pack w/ voice, 26 review/EA/hooks).
Owner rule: different ATB video in every Reel, repeats only with a gap -> atb.clip LRU, unused shuffled (tested full cycle).
