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
                     comments=int(st.get("commentCount", 0)))
        except Exception:
            pass
    if entry.get("instagram"):
        try:
            j = poster.call("GET", entry["instagram"], params={"fields": "like_count,comments_count"})
            m.update(likes=j.get("like_count", 0), comments=j.get("comments_count", 0))
            ins = poster.call("GET", f"{entry['instagram']}/insights", params={"metric": "views"})
            m.update(views=sum(v["values"][0]["value"] for v in ins.get("data", [])))
        except Exception:
            pass
    if entry.get("facebook"):
        try:
            j = poster.call("GET", entry["facebook"], params={"fields": "likes.summary(true),comments.summary(true)"})
            m.update(likes=j.get("likes", {}).get("summary", {}).get("total_count", 0),
                     comments=j.get("comments", {}).get("summary", {}).get("total_count", 0))
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
    if not force and (now.weekday() != 0 or st.get("growth_week") == week):  # Mondays, once
        return
    log = json.loads((ROOT / "content" / "posted.json").read_text(encoding="utf-8"))
    since = (now - dt.timedelta(days=8)).strftime("%Y-%m-%d")
    posts = []
    for e in log:
        if e.get("at", "") < since or not type_of(e):
            continue
        m = metrics(e)
        posts.append({"type": type_of(e), "kind": e["kind"], "score": score(m), **m})
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
    lines += ["", f"More of: **{st['boost'] or '—'}** · less of: **{st['drop'] or '—'}**",
              "", "Score = views + 10 × (likes + comments), summed over Facebook, Instagram and YouTube."]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    import sys
    assert rank([{"type": "a", "score": 10}, {"type": "a", "score": 30}, {"type": "b", "score": 5},
                 {"type": "b", "score": 7}, {"type": "c", "score": 999}]) == [("a", 20.0, 2), ("b", 6.0, 2)]
    assert type_of({"file": "output/queue/x/code_ABC_reel.mp4"}) == "code_reel"
    assert score({"views": 100, "likes": 3, "comments": 2}) == 150
    run(force="--now" in sys.argv)
