# FMM Design Playbook

Rules for every FMM image, Reel frame and cover. Learn principles only: never copy someone else's design or put a
Pinterest/Canva image into a post. FMM colours + logo + ATB stay in every post. Free tools only.
Sources (8 Nov 2026): our 13 live formats rendered from the real templates (output/design_now/), 5 Canva AI layout
references (assets/references/canva/, references only), assets/references/ (owner's picks).
**Pinterest is still to do**: the built-in browser pane was hidden, so pins didn't load, and the login box can't be passed
without an account. Re-run with the pane visible and add notes under "Pinterest" below.

## 1. Brand system (keep)
- Colours: black #050505 base, FMM red #E1062C, purple #8A2BE2, gold #FFD700 (only for #1, prices, winners),
  blue #2979FF, green #00C853 (good stats). One accent glow per post (ACCENTS in brand.py), not three.
- Fonts (all free, in assets/fonts): **Anton** = numbers + headlines (condensed, very bold, reads at phone size),
  **League Spartan** = titles, **Poppins SemiBold** = labels, **Inter** = small body. Max 2 per post: Anton + Poppins.
- Logo top-left. ATB badge bottom-right (atb.add_badge, 150 px). Thin accent strip at the very bottom.

## 2. What works (Canva references + top creators)
| Reference | Why it works | Use it for |
|---|---|---|
| Versus: split two-colour background, two heroes face to face, giant VS across the seam, stat rows in 2 columns | Instant "fight" reading, symmetry, one focal point (the VS) | versus, CR7 vs Messi |
| Top 10: a huge gold "1", then thin rows (rank, small photo, name, value right-aligned) | Hierarchy: #1 is the hero, the list is easy to scan | Top 10 by stat, Top 10 position |
| Event poster: one glowing card in the centre, energy shards behind it | Single subject + glow = depth on a flat background | leak / new event, hidden gem |
| Thumbnail: face fills ~45%, card top-right with glow, 2–3 huge words | Emotion + object + promise read in 0.5 s | Reel/Short covers (thumb.py) |
Weak parts we must NOT take: thin serif headlines, pink-on-purple low-contrast text, made-up placeholder data.

## 3. What our templates do worse (seen on output/design_now/)
1. **ATB badge covers content**: the review's "MUST BUY" stamp, the last value on versus and Top 4. → keep a 230×250 safe zone bottom-right.
2. Top 10 grid: owner prefers it (9 Nov); keep, only make sure ranks/stat pills stay readable.
3. **Review is crowded**: 9 panels, 14–20 px text (key stats, pros/cons, alternatives, rating meter). On a phone only the card reads.
4. **Budget XI parts are half empty**: 3 small cards in the middle, ~40% blank space.
5. **Versus has 12 thin rows** with red/green bars that read as "bad/good", not "left/right". → 6 face stats, winner in gold.
6. Footer CTA text (26 px grey) is too small to matter. → drop it or make it 34 px+.
7. Every format uses the same purple/blue glow → the feed looks samey. → one accent colour per format family.

## 4. Rules per format
- **All**: one focal point; nothing important in the bottom-right 230×250 (ATB) or the top 120 px right of the logo;
  numbers in Anton ≥ 44 px; labels ≥ 30 px; max ~25 words of on-image text; 60 px side margins.
- **Review**: big card (≈470×650) left, surname huge (Anton 120), OVR/POS line, 3 pros, one big verdict stamp
  (score/10 + verdict, green/gold/red), 6 face stats as big tiles. Full detail stays in the caption and the Reel.
- **Versus**: split background in two colours (diagonal), both cards big at the top, giant "VS" with glow, 6 face-stat rows,
  higher value in gold. Surnames in the title, not "stats comparison".
- **Top 10**: owner decision 9 Nov: keep the 3-4-3 card grid (cards + gold rank numbers + stat pill under each). The #1-hero + rows layout was tried and dropped.
- **Pick one / Choose 1**: cards as large as the grid allows; numbers 1–4 in Anton above each card; reaction emoji only
  as decoration (never "react to vote").
- **Budget XI part**: 3 cards fill the frame (2 top, 1 bottom), price pill under each, title = position ("Best Cheap Midfield").
- **Hidden gem / leak**: one glowing card + 3–5 stat bars or the sources line; "PREDICTION/LEAK" tag always visible.
- **Meme / ATB meme**: two rows, short text (≤4 words), ATB's reaction photo large; white panels keep it readable.
- **Covers (thumb.py)**: ATB face or the card fills ~45%, 2–3 words max, yellow/white text with black stroke, never black.

## 5. Stop doing
- Ten equal cards in a grid · tables with 12+ rows · grey 26 px footers · three different glows in one post ·
  text under the ATB badge · "Stats comparison"-style labels instead of names · empty space in the middle of a post.

## 6. Proposed upgrades (mocks in output/design_mocks/, *_before.png vs *_after.png, waiting for owner OK)
1. ~~Top 10 → #1 hero + rows~~ reverted 9 Nov, owner prefers the 3-4-3 grid
2. Versus → split colours, giant VS, 6 rows (brand.post_compare)
3. Budget XI part → 3 big cards + price pills (brand.post_xi_part)
4. Review → declutter: big card, verdict stamp, 6 tiles, 3 pros (brand.post_review)
5. ATB safe zone → every template keeps bottom-right 230×250 empty (all templates; check script)

## 7. Open-source techniques in use (8 Nov 2026)
- Photos: `brand.finish` = soft bloom on bright parts, vignette, fine mono grain (ideas from easy-pil and filmgrainer, written with numpy, no new package).
- Reels: `motion.progress_bar` = gold bar filling along the bottom edge (idea from shortsmith, ffmpeg only), added once per file in `poster.post`.
- Next candidates: word-by-word captions on clips with a voice (AI Video Captions: faster-whisper + ASS subtitles), only if we add voice-over Reels.
