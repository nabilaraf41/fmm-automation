---
name: fmm-savestate-hazard
description: fmm.savestate discards uncommitted code edits — commit code first; shard price copy must be refreshed from the PC
metadata:
  node_type: memory
  type: project
  originSessionId: b2f6976c-4048-4597-b0d1-56da525790d0
  modified: 2026-11-02T02:18:29.931Z
---

`python -m fmm.savestate` reset an uncommitted fmm/shards.py edit on 2 Nov 2026 (it resets the work tree while merging).
**Why:** it rebuilds state from origin and only keeps committed work.
**How to apply:** always `git commit` code before running savestate.

fcmobileforum's /api (ShardIQ prices) returns 403 to GitHub's servers. Don't bypass it (impersonating a browser was
refused as bot-check circumvention). The cloud uses content/shard_prices.json saved on the PC by
`python -m fmm.shards save` (valid 8 days; Windows task "FMM shard prices" runs Thursdays 20:00-22:00, owner uses the PC 8-10 pm), cross-checked live with fcmobilesquad.com (reachable from the cloud).
Links: [[fmm-automation-setup]]
