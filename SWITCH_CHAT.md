# Switching to a new chat (or another Claude)

Everything FMM knows lives in this folder:

| File | What it holds |
|---|---|
| CLAUDE.md | Handbook: how the system works + owner rules (read automatically) |
| HANDOVER.md | Latest status, fixes not to undo, open items |
| docs/memory/ | Memory notes (copy to `~/.claude/projects/E--Claude-FMM/memory/` on a new PC) |
| docs/history/ | Full text of every earlier chat, secrets removed (PC only, not on GitHub) |
| docs/CREATOR_PLAYBOOK.md | Creator rules (made by the research prompt below, if done) |
| SWITCH_CHAT.md | This file: all the prompts |

## 1. Before leaving a long chat (say this in the OLD chat)

```
Chat is getting long. Before I switch: update HANDOVER.md (status, fixes, open items), copy the memory notes to docs/memory/, export this chat with `python -m fmm.export_chat`, commit and push. Then tell me it's ready.
```

## 2. First message in a NEW Claude Code chat (folder E:\Claude\FMM)

```
Read HANDOVER.md, CLAUDE.md and the memory notes first. The full text of earlier chats is in docs/history/ — search it whenever I mention something from before, before asking me. Run `git pull` first. Then tell me in 5 lines what's running, what's open, and what I need to do. Keep following all my rules exactly as before.
```

## 3. If you switch to ANOTHER Claude (claude.ai, another account or PC) without this folder

Give it the repo (or upload CLAUDE.md, HANDOVER.md and docs/memory/*.md), then paste:

```
You're taking over FMM (FC Mobile Mania), my FC Mobile content automation. I'm the owner, ATB ("Araf The Boss"), in Bangladesh (BDT = UTC+6), zero budget, not technical: give me click-by-click steps and copy-paste commands, plain short English, result first.

Read the attached CLAUDE.md (handbook + rules), HANDOVER.md (status + open items) and the memory notes before doing anything. Everything posts from GitHub Actions in my private repo nabilaraf41/fmm-automation (only the cloud posts, never from a PC). Accounts: FB Page "FC Mobile Mania - FMM", IG @fc_fmm, YouTube "FC Mobile Mania - FMM".

My rules (mandatory):
- Cross-check every card/event/leak with a 2nd source before posting.
- ATB (me) in every post: face badge on photos, ATB clip on every Reel, facecam on long videos. Bright, realistic, glasses on, phone back only, never bald or dark.
- Every photo goes with its Reel: photo + Reel on Facebook and Instagram, Reel on YouTube Shorts. Different ATB clip in every Reel.
- Covers never black. No engagement bait. Facebook groups stay manual. Never commit or show tokens.
- Ask before anything that can't be undone (deleting, paying, sending).

Start by telling me in 5 lines what you understood and what's open.
```

## 4. Test that a new chat works like the old one

Knowledge test (answers come from the files):
```
Test: answer from CLAUDE.md, HANDOVER.md, memory notes, code and docs/history (search; don't guess; say "not found" if missing), 1–2 lines each, name the file:
1. My FB Page and IG IDs? 2. Which repo/workflow posts? 3. What starts the job hourly besides GitHub, and why? 4. Job time limit?
5. Where do secrets live? 6. Drive clips folder? 7. My time zone? 8. Every daily post time and what posts? 9. Thu/Sun 21:00?
10. The 19:00 series? 11. What posts at 13:00, which days? 12. Long video time and why? 13. Leak and ATB Meme times?
14. Cross-check rule and the function? 15. Posting from the PC? 16. Photo alone? 17. Which platforms, and why no photos on YouTube?
18. Banned caption bait? 19. Cover rules and what went wrong? 20. ATB rules per post type? 21. ATB look rules? 22. Same ATB clip every Reel?
23. How state is saved and the hazard? 24. Why commit before savestate? 25. FB Groups automated?
26. Pack Reel layout? 27. ATB Meme and its queue file? 28. How leaked cards are made, and why on the PC? 29. Who was left out of Week 4 and why?
30. What a long video gets? 31. Where goal times live? 32. EA Sports Logic Reel? 33. Focus players? 34. What the creator research says works?
35. 6 Nov timeout cause and fix? 36. Why IG missed posts and the fix? 37. Why the code Reel posted twice? 38. Why the FB cover failed?
39. Why the Reel caption is shorter? 40. The queue.py problem? 41. Flow account and voice? 42. Credit cost and reset date?
43. ATB asset folders? 44. My rule on different videos per Reel? 45. FB vs IG numbers on 8 Nov? 46. Photo + Reel on FB decision?
47. My two Facebook to-dos? 48. After the Flow credits reset? 49. YouTube API + IG replies status? 50. Duplicate posts to delete?
```

Judgment test (describe only, don't run or post anything):
```
Say what you'd do, step by step, 3–5 lines each, DON'T run or post anything:
1. "Post the new 125 Messi card now", one YouTube source. 2. "Test the 21:00 Reel on the PC". 3. A cloud run timed out at 100 min.
4. IG got a post, FB didn't. 5. I upload "pack ronaldo 125.mp4". 6. I upload an 8-min "long h2h …". 7. "Leak: 125 Pelé CAM from MadridistaaFC".
8. A meme idea: top "my 110 team", bottom "opponent's 125 team", label "ME". 9. Changing featured.json while the cloud may be saving.
10. Edited slots.py and need to save state: order and why? 11. A cover came out black. 12. "Why is Facebook still getting no views?"
13. Flow credits reset. 14. A Reel would go out without ATB. 15. My token is in a log. 16. "Delete all old duplicates".
17. "kal post hoi nai keno?" 18. Wrong stats on a review photo. 19. "Make the Reel 4K". 20. What you do before saying "done".
21. Unsure what I decided earlier. 22. GitHub skipped 3 runs: is a slot lost? 23. Everything a new photo format must touch.
24. Chat getting long. 25. How you talk to me, in one paragraph.
```
Paste the answers into the old chat (or check them against CLAUDE.md/HANDOVER.md). Anything missing gets written into the files.

## 5. Make it work like a big creator (research → playbook)

```
Goal: run FMM like a top FC Mobile creator who earns a lot. Save everything in files.
1. RESEARCH (vidIQ, YouTube/IG search, web; real numbers only): top 15 FC Mobile creators on YT Shorts, long YT, IG and FB (BD, India, Indonesia, global): median views, posting times and frequency, length, 2-second hook, title/thumbnail/caption style, how they earn. Their 30 best videos of the last 60 days and why each worked. What gets FC Mobile Pages reach on Facebook now. Money: YPP (1,000 subs + 4,000 h or 10M Shorts views), FB/IG monetization, sponsors, top-up/code affiliates, and what FMM is missing. Build on memory notes fc-mobile-top-creators, rkreddy-research, fc-mobile-evergreen-shorts and CONTENT_STRATEGY.md.
2. COMPARE with our numbers (content/weekly_report.md, posted.json, vidIQ): what we do differently, ranked by views lost.
3. WRITE docs/CREATOR_PLAYBOOK.md (short rules: hooks, titles, covers, length, times per platform, formats more/less, FB growth plan, money milestones, a before-every-post checklist). Add to CLAUDE.md: "Follow docs/CREATOR_PLAYBOOK.md for every post; update it from the Monday growth report."
4. PROPOSE the top 5 automation changes (biggest gain first). Don't change code yet; wait for my OK.
My rules still apply.
```
Keep it improving: every Monday "read this week's growth report and update the playbook"; when a video blows up "study this video: <link> and add what works"; monthly "redo the creator research".

## 6. Owner's to-do list (things only you can do)

1. Facebook app → switch to the FMM Page → Professional dashboard → Page status → send the screenshot.
2. Share 1–2 Reels a day to FC Mobile Facebook groups and your profile.
3. Upload a "long …" match → tell Claude so it marks the goal times.
4. See a leak → send the screenshot.
5. Around 26–29 Nov → tell Claude "Flow credits reset".
6. New PC → copy docs/memory/*.md to `C:\Users\<you>\.claude\projects\E--Claude-FMM\memory\`, and the .env file + secrets/ folder by hand (they're not on GitHub).
