---
name: fmm-ig-skills
description: Instagram agent skills (ig-*) installed for FMM; owner wants them used proactively with reports when important
metadata:
  node_type: memory
  type: feedback
  originSessionId: b2f6976c-4048-4597-b0d1-56da525790d0
  modified: 2026-10-31T18:36:10.645Z
---

13 ig-* skills (github.com/Jakeschincariol/instagram-agent-skill, MIT) are installed in E:\Claude\FMM\.claude\skills;
voice profile at ~/.claude/instagram/voice.md (FMM brand). The humanizer + caption rules run automatically on every
post (fmm/captions.py, vendored in fmm/vendor/).

**Why:** owner said (1 Nov 2026) "use these skills and commands and report on your own whenever important".
**How to apply:** when checking in, run /ig-audit on recent posts (or the Monday weekly_report.md), /ig-plan for the
week and /ig-profile when they share a profile screenshot; report findings unprompted when something matters
(a drop, a winning format, a fix). Never let the skills post or DM — they draft; the pipeline posts. See [[fmm-automation-setup]].
