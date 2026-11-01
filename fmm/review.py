"""FMM player reviews written from stats, following the FMM Player Review Standard.

review(player) -> dict(pros, cons, score, verdict, formations, caption, summary)
Original FMM wording; only facts (OVR, stats, playstyles) come from the database.
"""
import random

GROUPS = {
    "att": {"pos": {"ST", "CF", "LW", "RW", "LF", "RF"},
            "keys": ["fin", "pos", "acc", "spd", "sho", "dri", "bac", "agi", "hea", "str", "lsa", "rea"]},
    "mid": {"pos": {"CAM", "CM", "CDM", "LM", "RM"},
            "keys": ["spa", "lpa", "vis", "bac", "dri", "sta", "rea", "awr", "stt", "lsa", "agi", "str"]},
    "def": {"pos": {"CB", "LB", "RB", "LWB", "RWB"},
            "keys": ["awr", "stt", "slt", "mrk", "str", "jmp", "hea", "spd", "acc", "agg", "spa", "rea"]},
    "gk": {"pos": {"GK"}, "keys": ["ref", "gkd", "gkh", "gkp", "gkk", "rea"]},
}

STRENGTH = {
    "fin": "Elite finishing — chances inside the box rarely go wasted",
    "pos": "Smart off-ball runs that find space behind the line",
    "acc": "Explosive acceleration to beat defenders over the first few metres",
    "spd": "Top-end pace for counter attacks and through balls",
    "sho": "Powerful shots that beat keepers from distance",
    "lsa": "Dangerous long shots from outside the box",
    "dri": "Tight dribbling in crowded areas",
    "bac": "Clean first touch and close control under pressure",
    "agi": "Sharp turns and quick changes of direction",
    "hea": "Strong in the air — a real threat from crosses",
    "str": "Physical presence that wins shoulder-to-shoulder duels",
    "rea": "Quick reactions to loose balls and rebounds",
    "spa": "Reliable short passing that keeps possession ticking",
    "lpa": "Accurate long balls that switch play instantly",
    "vis": "Creative vision to unlock tight defences",
    "sta": "Huge stamina — still pressing in the 90th minute",
    "awr": "Excellent defensive awareness and positioning",
    "stt": "Clean standing tackles that win the ball back",
    "slt": "Well-timed sliding tackles as a last line of defence",
    "mrk": "Tight marking that keeps strikers quiet",
    "jmp": "Great leap for aerial duels at both ends",
    "agg": "Aggressive pressing that forces mistakes",
    "ref": "Lightning reflexes on close-range shots",
    "gkd": "Big diving range to reach corner shots",
    "gkh": "Safe hands that rarely spill the ball",
    "gkp": "Good positioning that makes saves look easy",
    "gkk": "Long, accurate kicks to start attacks",
}
WEAKNESS = {
    "fin": "Finishing can be inconsistent in big moments", "pos": "Off-ball movement is only average",
    "acc": "Slow to get going over short distances", "spd": "Lacks top-end pace against fast defenders",
    "sho": "Shot power is limited from range", "lsa": "Not a long-shot threat", "dri": "Dribbling feels heavy in tight spaces",
    "bac": "First touch can let him down under pressure", "agi": "Turns can feel slow and stiff",
    "hea": "Not a reliable target for crosses", "str": "Can be pushed off the ball by strong defenders",
    "rea": "Reactions are a step behind the elite cards", "spa": "Short passing is only average",
    "lpa": "Long passing is inconsistent", "vis": "Limited creativity in the final third",
    "sta": "Stamina drops late in matches", "awr": "Defensive positioning can be caught out",
    "stt": "Standing tackles are not his strength", "slt": "Risky in sliding tackles", "mrk": "Marking can be loose",
    "jmp": "Struggles in aerial duels", "agg": "Low aggression when pressing", "ref": "Reflexes are average",
    "gkd": "Limited diving range", "gkh": "Handling can be shaky", "gkp": "Positioning errors on angled shots",
    "gkk": "Kicking distance is limited",
}
FORMATIONS = {"att": ["4-3-3 Attack", "4-2-3-1", "4-1-2-1-2"], "mid": ["4-3-3 Holding", "4-2-3-1", "4-1-2-1-2 Narrow"],
              "def": ["4-3-3", "4-2-3-1", "5-3-2"], "gk": ["Any formation"]}
HOOKS = ["🔥 Is {ovr} OVR {name} worth it?", "🚨 {ovr} {name} just dropped — should you get him?",
         "👀 {name} {ovr} OVR: hype or must-have?", "⚡ Full review: {ovr} OVR {name} ({pos})"]
WR = {1: "Low", 2: "Medium", 3: "High"}


FACE = {"PAC": ["acc", "spd"], "SHO": ["fin", "sho", "lsa", "pos", "vol"], "PAS": ["spa", "lpa", "vis", "cro", "cur"],
        "DRI": ["dri", "agi", "bal", "rea", "bac"], "DEF": ["awr", "stt", "slt", "mrk"], "PHY": ["str", "jmp", "sta", "agg"]}
DETAIL = [("PACE", [("acc", "Acceleration"), ("spd", "Sprint Speed")]),
          ("SHOOTING", [("fin", "Finishing"), ("sho", "Shot Power"), ("lsa", "Long Shots"), ("pos", "Positioning")]),
          ("PASSING", [("spa", "Short Passing"), ("lpa", "Long Passing"), ("vis", "Vision")]),
          ("DRIBBLING", [("dri", "Dribbling"), ("agi", "Agility"), ("bac", "Ball Control"), ("rea", "Reactions")]),
          ("DEFENDING", [("awr", "Awareness"), ("stt", "Standing Tackle"), ("slt", "Sliding Tackle")]),
          ("PHYSICAL", [("str", "Strength"), ("jmp", "Jumping"), ("sta", "Stamina")])]


def face_stats(p):
    """PAC/SHO/PAS/DRI/DEF/PHY averages from the detailed stats."""
    st = p.get("stats") or {}
    out = {}
    for k, ks in FACE.items():
        vals = [st[x] for x in ks if x in st]
        out[k] = round(sum(vals) / len(vals)) if vals else 0
    return out


def group(pos):
    for g, v in GROUPS.items():
        if pos in v["pos"]:
            return g
    return "mid"


def key_avg(p, g):
    st = p.get("stats") or {}
    ks = [k for k in GROUPS[g]["keys"][:6] if k in st]
    return sum(st[k] for k in ks) / len(ks) if ks else 0


def review(p, pool=None, seed=None):
    """pool = other players (dicts) to rank against; the score is this card's percentile in its position group."""
    rnd = random.Random(seed or p.get("id"))
    g = group(p.get("pos", ""))
    st = p.get("stats") or {}
    keys = [k for k in GROUPS[g]["keys"] if k in st]
    ranked = sorted(keys, key=lambda k: st[k], reverse=True)
    best = st[ranked[0]] if ranked else 0
    # stamina sits on a different scale in FC Mobile, so it only counts as a weakness when truly low
    low = [k for k in ranked[::-1] if (k != "sta" or st[k] < 55) and st[k] < best - 10][:2]
    top = ranked[:3]
    peers = [x for x in (pool or []) if group(x.get("pos", "")) == g and x.get("stats")]
    me = key_avg(p, g)
    pct = (sum(key_avg(x, g) <= me for x in peers) / len(peers)) if len(peers) >= 3 else 0.6
    bonus = (0.5 if (p.get("weak_foot") or 0) >= 4 else 0) + (0.25 if (p.get("skill_moves") or 0) >= 4 else 0)
    score = round(min(9.5, max(6.0, 6.5 + 2.5 * pct + bonus)) * 2) / 2
    verdict = "MUST BUY" if score >= 9 else "WORTH IT" if score >= 8 else "SITUATIONAL" if score >= 7 else "SKIP"
    pros = [STRENGTH[k].split(" —")[0] for k in top]
    cons = [WEAKNESS[k] for k in low] or ["No major weaknesses at this rating"]
    name, ovr, pos = p.get("name", ""), p.get("ovr"), p.get("pos", "")
    hook = rnd.choice(HOOKS).format(name=name, ovr=ovr, pos=pos)
    forms = FORMATIONS[g]
    ps = ", ".join(p.get("playstyles") or []) or "—"
    summary = (f"{name} is built for a {('direct, goal-hungry' if g == 'att' else 'controlling' if g == 'mid' else 'solid, no-nonsense' if g == 'def' else 'reliable')} "
               f"role. His best tools are {STRENGTH[top[0]].split(' —')[0].lower()} and {STRENGTH[top[1]].split(' —')[0].lower()}"
               if len(top) >= 2 else f"{name} is a solid all-round option.")
    wf, sm = p.get("weak_foot"), p.get("skill_moves")
    wr = p.get("work_rates") or [None, None]
    who = {"att": "players who love fast attacks and need a reliable goal threat",
           "mid": "players who build through midfield and want control",
           "def": "players who need a dependable defensive anchor",
           "gk": "anyone who needs a dependable last line"}[g]
    caption = "\n".join([
        hook, "",
        f"📋 {ovr} OVR {name} – {pos}" + (f" | WF {('★' * wf + '☆' * (5 - wf))}" if isinstance(wf, int) else "")
        + (f" | SM {('★' * sm + '☆' * (5 - sm))}" if isinstance(sm, int) else ""),
        f"🎯 PlayStyles: {ps}", "",
        f"{summary}.", "",
        "✅ Strengths", *[f"• {STRENGTH[k]}" for k in top], "",
        "❌ Weaknesses", *[f"• {c}" for c in cons], "",
        f"🧩 Best formations: {', '.join(forms)}",
        (f"⚙️ Work rates: {WR.get(wr[0], '?')}/{WR.get(wr[1], '?')}" if wr[0] else ""), "",
        f"⭐ FMM Rating: {score}/10 — {verdict}",
        f"Best for {who}.", "",
        "👇 Would he make your starting XI?", "",
        "(Stat-based FMM review.)", "",
        f"#FCMobile #FCMobile26 #EASportsFCMobile #PlayerReview #{(name or '').replace(' ', '').replace('.', '')} #FMM",
    ]).replace("\n\n\n", "\n\n")
    label = {k: l for _, rows in DETAIL for k, l in rows} | {"vol": "Volleys", "hea": "Heading", "mrk": "Marking",
             "agg": "Aggression", "ref": "Reflexes", "gkd": "Diving", "gkh": "Handling", "gkp": "GK Positioning", "gkk": "Kicking"}
    short_pros = [f"{label.get(k, k.upper())} {st[k]}" for k in top]
    short_cons = [f"{label.get(k, k.upper())} {st[k]}" for k in low] or ["No real weakness"]
    return {"pros": pros, "cons": cons, "short_pros": short_pros, "short_cons": short_cons, "score": score, "verdict": verdict, "formations": forms,
            "summary": summary, "caption": caption, "group": g}


if __name__ == "__main__":
    import json, sys
    from pathlib import Path
    db = json.loads((Path(__file__).resolve().parent.parent / "content" / "players_db.json").read_text(encoding="utf-8"))
    pool = list(db["players"].values())
    for p in pool[:6]:
        r = review(p, pool)
        print(p["ovr"], p["pos"], p["name"], "->", r["score"], r["verdict"], "| cons:", r["cons"])
