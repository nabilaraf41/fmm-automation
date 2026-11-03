"""Weekly growth loop (Mondays): learn which post types work and post more of them.

Reads last week's posts from content/posted.json, fetches results (YouTube views, Instagram views/likes/comments,
Facebook likes/comments), scores each post type, writes content/weekly_report.md and sets
featured.json -> "boost" (best photo format, gets extra turns) and "drop" (worst, skipped) for the photo rotation.
"""
import collections, datetime as dt, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "content" / "weekly_report.md"


def score(m):
    """One number per post: views count once, likes/comments count 10x (they push reach)."""
    return m.get("views", 0) + 10 * (m.get("likes", 0) + m.get("comments", 0))


def rank(posts):
    """[(type, avg_score, n)] best first; types with fewer than 2 posts are ignored."""
    by = collections.defaultdict(list)
    for p in posts:
        by[p["type"]].append(p["score"])
    return sorted(((t, sum(v) / len(v), len(v)) for t, v in by.items() if len(v) >= 2), key=lambda x: -x[1])


def metrics(entry):
    from fmm import poster
    m = collections.Counter()
    if entry.get("youtube"):
        try:
            from fmm import youtube
            st = youtube.service().videos().list(part="statistics", id=entry["youtube"]).execute()["items"][0]["statistics"]
            m.update(views=int(st.get("viewCount", 0)), likes=int(st.get("likeCount", 0)),
                     comments=int(st.get("commentCount", 0)), yt_views=int(st.get("viewCount", 0)))
        except Exception:
            pass
    if entry.get("instagram"):
        try:
            j = poster.call("GET", entry["instagram"], params={"fields": "like_count,comments_count"})
            m.update(likes=j.get("like_count", 0), comments=j.get("comments_count", 0),
                     ig_eng=j.get("like_count", 0) + j.get("comments_count", 0))
        except Exception:
            pass
        try:  # needs instagram_manage_insights on the token; without it Instagram views stay 0
            ins = poster.call("GET", f"{entry['instagram']}/insights", params={"metric": "views"})
            v = sum(x["values"][0]["value"] for x in ins.get("data", []))
            m.update(views=v, ig_views=v)
        except Exception:
            pass
    if entry.get("facebook"):
        try:
            j = poster.call("GET", entry["facebook"], params={"fields": "likes.summary(true),comments.summary(true)"})
            m.update(likes=j.get("likes", {}).get("summary", {}).get("total_count", 0),
                     comments=j.get("comments", {}).get("summary", {}).get("total_count", 0))
            m.update(fb_eng=j.get("likes", {}).get("summary", {}).get("total_count", 0)
                     + j.get("comments", {}).get("summary", {}).get("total_count", 0))
            if entry.get("kind") == "reel":  # Reel ids are videos: Facebook shares their view count
                v = poster.call("GET", entry["facebook"], params={"fields": "views"}).get("views", 0)
                m.update(views=v, fb_views=v)
        except Exception:
            pass
    return m


def type_of(e):
    """Logged type, or guessed from the file name for posts made before types were logged."""
    if e.get("type"):
        return e["type"]
    n = Path(e.get("file", "").replace("\\", "/")).name.lower()
    return ("roundup" if n.startswith("codes_roundup") else "code_reel" if n.startswith("code_") and n.endswith(".mp4")
            else "code" if n.startswith("code_") else "pack" if n.startswith("pack") else None)


def run(force=False):
    from fmm import slots
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=6)))
    st = slots.load_state()
    week = now.strftime("%G-W%V")
    if not force and (now.weekday() != 1 or now.hour < 20 or st.get("growth_week") == week):  # owner: Tuesday night, once
        return
    log = json.loads((ROOT / "content" / "posted.json").read_text(encoding="utf-8"))
    since = (now - dt.timedelta(days=8)).strftime("%Y-%m-%d")
    posts = []
    for e in log:
        if e.get("at", "") < since or not type_of(e):
            continue
        m = metrics(e)
        posts.append({"type": type_of(e), "kind": e["kind"], "score": score(m), "at": e["at"][:10],
                      "hour": e["at"][11:13], **m})
    ranked = rank(posts)
    rotation = {"review_post", "rank10", "versus", "pick3", "guess", "compare4", "xi", "rate", "gem", "worth", "meme"}
    photo = [r for r in ranked if r[0] in rotation]  # only formats the photo slots can actually schedule
    st["growth_week"] = week
    st["boost"] = photo[0][0] if photo else None
    st["drop"] = photo[-1][0] if len(photo) >= 4 else None  # only drop when there's enough to compare
    slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    lines = [f"# FMM weekly report — {week}", "", f"{len(posts)} posts checked.", "",
             "| Type | Avg score | Posts |", "|---|---|---|"]
    lines += [f"| {t} | {s:.0f} | {n} |" for t, s, n in ranked]
    tot = lambda k: sum(p.get(k, 0) for p in posts)
    lines += ["", "## By platform", "", "| Platform | Views | Likes + comments |", "|---|---|---|",
              f"| YouTube | {tot('yt_views'):,} | — |", f"| Instagram | (needs insights permission) | {tot('ig_eng'):,} |",
              f"| Facebook (Reels) | {tot('fb_views'):,} | {tot('fb_eng'):,} |"]
    by_hour = collections.defaultdict(list)
    for p in posts:
        by_hour[p["hour"]].append(p["score"])
    lines += ["", "## By posting hour (BDT)", "", "| Hour | Avg score | Posts |", "|---|---|---|"]
    lines += [f"| {h}:00 | {sum(v) / len(v):.0f} | {len(v)} |" for h, v in sorted(by_hour.items())]
    lines += ["", "## Top 5 posts", ""] + [f"{i}. {p['at']} {p['type']} ({p['kind']}): score {p['score']:,}"
                                           for i, p in enumerate(sorted(posts, key=lambda p: -p["score"])[:5], 1)]
    lines += ["", f"More of: **{st['boost'] or '—'}** · less of: **{st['drop'] or '—'}**",
              "", "Score = views + 10 × (likes + comments), summed over Facebook, Instagram and YouTube."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def to_docx(folder=r"D:\FMM INFOS\DOCS"):
    """PC only: this week's report as a Word file in the owner's folder, opened on screen once."""
    import os, docx
    text = REPORT.read_text(encoding="utf-8").splitlines()
    out = Path(folder) / f"FMM weekly report {text[0].split('—')[-1].strip()}.docx"
    if out.exists():
        return
    d = docx.Document()
    rows = []
    for line in text + [""]:
        if line.startswith("|"):  # markdown table -> Word table
            if not set(line) <= set("|-"):
                rows.append([c.strip() for c in line.strip("|").split("|")])
            continue
        if rows:
            t = d.add_table(rows=0, cols=len(rows[0]), style="Light Grid Accent 1")
            for r in rows:
                for c, v in zip(t.add_row().cells, r):
                    c.text = v
            rows = []
        if line.startswith("#"):
            d.add_heading(line.lstrip("# "), level=1 if line.startswith("# ") else 2)
        elif line:
            d.add_paragraph(line.replace("**", ""))
    out.parent.mkdir(parents=True, exist_ok=True)
    d.save(out)
    os.startfile(out)
    print("report saved:", out)


if __name__ == "__main__":
    import sys
    if "--pc" in sys.argv:  # Tuesday-night PC task: make the report if the cloud hasn't yet, then the Word file
        run()
        week = dt.datetime.now(dt.timezone(dt.timedelta(hours=6))).strftime("%G-W%V")
        if REPORT.exists() and week in REPORT.read_text(encoding="utf-8").splitlines()[0]:  # only this week's report
            to_docx()
        sys.exit()
    assert rank([{"type": "a", "score": 10}, {"type": "a", "score": 30}, {"type": "b", "score": 5},
                 {"type": "b", "score": 7}, {"type": "c", "score": 999}]) == [("a", 20.0, 2), ("b", 6.0, 2)]
    assert type_of({"file": "output/queue/x/code_ABC_reel.mp4"}) == "code_reel"
    assert score({"views": 100, "likes": 3, "comments": 2}) == 150
    run(force="--now" in sys.argv)
