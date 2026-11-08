---
name: fmm-atb-meme
description: "ATB Meme" format (owner's NO/YES template) — owner names the right side, Claude queues it
metadata:
  type: project
---

Owner (7 Nov 2026) wants to post the "ATB Meme" a lot: ATB says NO (top) / YES (bottom) on the left, two things on the right,
optional label like "EA". The owner tells Claude what goes on the right each time; Claude adds
{top, bottom, label, caption?} to content/atb_meme.json → queue (cards "Name OVR POS", confirmed only; "img:<file>"
from assets/atb_meme/items/; or text), commits, and runs savestate if needed. fmm.atbmeme posts one a day at 15:00 BDT
(photo + auto Reel with an ATB clip). ATB images: assets/atb_meme/no.jpg, yes.jpg (Flow nabilaraf24, brightened).
Test render: python -m fmm.atbmeme test "Ronaldo 124 ST" "Gullit 124 CM" EA
Links: [[fmm-atb-host]] [[fmm-cross-check]] [[fmm-photo-plus-reel]]
