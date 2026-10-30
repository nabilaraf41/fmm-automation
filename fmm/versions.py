""""EA Sports Logic" posts: two versions of the same player, one great and one a waste.

Pairs come from content/card_library.json (RenderZ history, built on the PC: python -m fmm.versions collect).
A pair is funniest when the LOWER-OVR card has the BETTER key stats (like 111 Cruyff > 113 Cruyff).
Focus players (CR7, Messi, Neymar, Kane, BD and Indian players) are picked first.

    python -m fmm.versions collect    -> (PC only) refresh library + build card images for candidate pairs
    python -m fmm.versions pairs      -> list the best pairs
Reel layout: top half = the two cards (GOAT ✅ / WASTE ❌), bottom half = a meme clip you upload to the Drive
folder with a name starting "meme" (e.g. "meme ea sports.mp4"); its audio is used.
"""
import collections, json, sys, time
from pathlib import Path

from fmm import renderz, review as rv

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "content" / "card_library.json"
FOCUS = ["ronaldo", "messi", "neymar", "kane", "hamza", "chhetri", "jhingan", "sandesh", "gurpreet", "mbappé", "yamal"]


def library():
    return json.loads(LIB.read_text(encoding="utf-8"))["players"] if LIB.exists() else {}


def pairs(limit=20):
    lib = library()
    by = collections.defaultdict(list)
    for p in lib.values():
        if p.get("stats") and (renderz.CARDS / f"{p['id']}.png").exists() or "--all" in sys.argv:
            by[p["name"]].append(p)
    out = []
    for name, cards in by.items():
        uniq = {(c["ovr"], c.get("program")): c for c in cards}.values()
        cards = sorted(uniq, key=lambda c: c["ovr"])
        if len(cards) < 2:
            continue
        g = rv.group(cards[0].get("pos", ""))
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                lo, hi = cards[i], cards[j]
                d = rv.key_avg(lo, g) - rv.key_avg(hi, g)
                good, bad = (lo, hi) if d > 0 else (hi, lo)
                irony = d > 0 and hi["ovr"] > lo["ovr"]          # lower OVR but better: "EA logic"
                focus = any(f in name.lower() for f in FOCUS)
                out.append(((focus, irony, abs(d)), name, good, bad, irony))
    out.sort(key=lambda o: o[0], reverse=True)
    seen, res = set(), []
    for _, name, good, bad, irony in out:
        if name not in seen:
            seen.add(name); res.append({"name": name, "good": good, "bad": bad, "irony": irony})
        if len(res) >= limit:
            break
    return res


def new_vs_old(new_cards, min_gap=3.0):
    """For each NEW card, compare with the same player's older versions.
    Worth a Reel only if the stat gap is clear (>= min_gap on key stats). Best story first:
      new card has higher OVR but WORSE stats  -> "EA Sports Logic" (old one is the GOAT)
      new card is much better                   -> "Upgrade" (new one is the GOAT)"""
    lib = library()
    out = []
    for n in new_cards:
        old = [p for p in lib.values() if p.get("name") == n.get("name") and p.get("stats")
               and str(p["id"]) != str(n["id"]) and (p.get("added") or "") < (n.get("added") or "9")]
        if not old or not n.get("stats"):
            continue
        g = rv.group(n.get("pos", ""))
        for o in old:
            d = rv.key_avg(n, g) - rv.key_avg(o, g)
            if abs(d) < min_gap:
                continue
            irony = d < 0 and (n.get("ovr") or 0) >= (o.get("ovr") or 0)
            good, bad = (n, o) if d > 0 else (o, n)
            out.append(((irony, abs(d)), {"name": n["name"], "good": good, "bad": bad, "irony": irony, "new": n}))
    out.sort(key=lambda x: x[0], reverse=True)
    seen, res = set(), []
    for _, pr in out:
        if pr["name"] not in seen:
            seen.add(pr["name"]); res.append(pr)
    return res


def collect(pages=60):
    """PC: fetch RenderZ history, keep facts, build card images for the best pairs (+ mark programs confirmed)."""
    lib, imgs = {}, {}
    for pg in range(1, pages + 1):
        try:
            page = renderz.fetch(renderz.LIST_URL + f"&page={pg}").decode("utf-8", "ignore")
            ps = [renderz.slim(x) for x in renderz.extract_array(page)]
        except Exception as ex:
            print("stopped at page", pg, str(ex)[:60]); break
        for p in ps:
            imgs[str(p["id"])] = p
            lib[str(p["id"])] = {k: v for k, v in p.items() if k not in ("img_player", "img_bg")}
        time.sleep(1.5)
    LIB.write_text(json.dumps({"players": lib}, ensure_ascii=False), encoding="utf-8")
    sys.argv.append("--all")
    best = pairs(40)
    made = 0
    for pr in best:
        for c in (pr["good"], pr["bad"]):
            path = renderz.CARDS / f"{c['id']}.png"
            if not path.exists() and str(c["id"]) in imgs:
                renderz.build_card(imgs[str(c["id"])]).save(path); made += 1; time.sleep(1)
    from fmm import slots
    st = slots.load_state()
    progs = {(p.get("program") or "").replace("PROGRAM_", "") for p in lib.values()} - {""}
    st["confirmed_programs"] = sorted(set(st.get("confirmed_programs", [])) | progs)
    st["hold_programs"] = [h for h in st.get("hold_programs", []) if h not in progs]
    slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"library: {len(lib)} cards | card images built: {made} | confirmed programs: {len(progs)}")


def top_panel(pr, path, w=1080, h=960):
    """Top half: two cards side by side, GOAT ✅ under the good one, WASTE ❌ under the bad one."""
    from PIL import Image, ImageDraw
    from fmm.brand import base, fit_card, font, label_font, GREEN, RED, WHITE, GOLD
    img, d, _ = base("comparison", None, (w, h))
    good, bad = pr["good"], pr["bad"]
    order = sorted([good, bad], key=lambda c: c["ovr"])          # lower OVR on the left, like the reference
    for i, c in enumerate(order):
        x = 40 + i * (w // 2)
        card = fit_card(str(renderz.CARDS / f"{c['id']}.png"), w // 2 - 80, 640, GREEN if c is good else RED)
        img.paste(card, (x - 30 + (w // 2 - 80 - (card.width - 60)) // 2, 60), card)
        d = ImageDraw.Draw(img)
        tag, col = ("GOAT", GREEN) if c is good else ("WASTE", RED)
        cx = x + (w // 2 - 80) // 2
        d.rounded_rectangle((cx - 170, 760, cx + 170, 860), 50, fill=col)
        d.text((cx, 810), tag, font=font("Anton-Regular.ttf", 72), fill=WHITE, anchor="mm")
        from fmm.slots import program_name
        d.text((cx, 900), f"{c['ovr']} OVR • {program_name(c.get('program'))}".upper(), font=label_font(30),
               fill=GOLD, anchor="mm")
    img.convert("RGB").save(path)
    return path


def make_reel(pr, meme, out_dir, seconds=None):
    """Top: cards panel; bottom: meme clip (with its audio). Writes <out>/slot.mp4 + slot_cover.jpg."""
    import subprocess
    from fmm import clips, thumb
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    top = top_panel(pr, out_dir / "_top.png")
    dur = min(seconds or clips.duration(meme), 25)
    out = out_dir / "slot.mp4"
    fc = ("[0:v]scale=1080:960,setsar=1[t];"
          "[1:v]scale=1080:960:force_original_aspect_ratio=increase,crop=1080:960,setsar=1[b];"
          "[t][b]vstack=inputs=2,format=yuv420p[v]")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(top), "-i", str(meme),
                        "-filter_complex", fc, "-map", "[v]", "-map", "1:a?", "-t", f"{dur:.2f}", "-r", "30",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k",
                        "-movflags", "+faststart", str(out)], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    thumb.cover(str(top), "EA SPORTS\nLOGIC 🤡".replace(" 🤡", "!?"), out_dir / "slot_cover.jpg",
                sub=f"{pr['name']} {pr['good']['ovr']} > {pr['bad']['ovr']}?!", color="red", emoji=None)
    top.unlink(missing_ok=True)
    return out


def caption(pr):
    g, b = pr["good"], pr["bad"]
    from fmm.slots import program_name
    gs, bs = rv.face_stats(g), rv.face_stats(b)
    better = [k for k in gs if gs[k] > bs[k]]
    return (f"EA Sports Logic 🤡🤣 {g['ovr']} vs {b['ovr']} {pr['name']}\n\n"
            f"✅ {g['ovr']} {pr['name']} ({program_name(g.get('program'))})\n"
            f"❌ {b['ovr']} {pr['name']} ({program_name(b.get('program'))})\n\n"
            f"The {g['ovr']} wins on {', '.join(better) or 'the stats'}"
            + (f" — even with LOWER OVR!" if pr["irony"] else "") +
            "\n\nWhich version do you have? 👇\n\n#FCMobile #FCMobile26 #EASportsFCMobile #EASportsLogic #FMM")


if __name__ == "__main__":
    if sys.argv[1:2] == ["collect"]:
        collect()
    else:
        for p in pairs():
            print(f"{p['name']:16} GOOD {p['good']['ovr']} {p['good']['program']:22} BAD {p['bad']['ovr']} "
                  f"{p['bad']['program']:22} {'EA LOGIC' if p['irony'] else ''}")
