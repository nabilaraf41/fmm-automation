---
name: fmm-design-references
description: "Post formats the FMM owner showed as references (VS stats, top-4 table, pick-one react, spotlight, top-10 grid) and the clip rule"
metadata:
  node_type: memory
  type: feedback
  originSessionId: b2f6976c-4048-4597-b0d1-56da525790d0
  modified: 2026-10-30T21:22:49.129Z
---

Reference images live in E:\Claude\FMM\assets\references\ — rebuild them in FMM brand (black/red/gold, FMM logo), never copy other creators' branding:
- vs_1v1_stats.png → 1 vs 1 comparison: two cards on top, 6 face stats (PAC SHO PAS DRI DEF PHY), full stat list, green = better / red = worse.
- vs_top4_table.png → Top 4 of one position: 4 cards on top, rows of face stats, best value highlighted.
- pick_one_react.png → "Pick one" post: 3 tall card panels, a reaction emoji (Love/Wow/Haha) under each.
- spotlight.jpg, react_battle.jpg, top10_grid.jpg → spotlight, react battle, top-10 grid formats.
Clip rule: every gameplay video Reel and its cover must show the card of the player who scored / played well (taken from the file name).

**Why:** owner's explicit direction (Oct 2026).
**How to apply:** templates are in fmm/brand.py (post_compare, post_compare4, post_pick3, …); match these when adding formats. See [[fmm-user-preferences]].
