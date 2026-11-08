---
name: fmm-no-pc-posting
description: "Never post or run fmm.run_cloud / slots.post from the owner's PC — the cloud is the only poster"
metadata:
  node_type: memory
  type: feedback
  originSessionId: b2f6976c-4048-4597-b0d1-56da525790d0
  modified: 2026-11-03T10:27:31.340Z
---

Never run anything that posts from the PC (slots.post, poster.post, `python -m fmm.run_cloud`, even "to test").
**Why:** on 2 Nov a PC post + the cloud post made a duplicate; on 3 Nov `python -m fmm.run_cloud --selfcheck`
started a real run (args are ignored) and had to be killed. Owner said "stop my pc" (3 Nov 2026).
**How to apply:** test with `slots.build_extra(...)`/`slots.build(...)` only, then `git checkout`/stash content;
for real posting use the cloud (dated `force` overrides in featured.json, or dispatch codes.yml).
Links: [[fmm-savestate-hazard]]
