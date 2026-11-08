"""Leaks / predictions of cards that are not out yet, made like FC Mobile Forum does it:
the player's render from an older card on the new event's card background, with the leaked OVR and position.

Cards are built on the PC (RenderZ blocks the cloud) into assets/cards/leaks/, together with the post image;
the cloud then posts it (photo + its Reel on FB, IG, YT) once a day at 11:00 BDT.
Owner rule: a leak goes out only when 2 sources name it (sources list in the queue item).

content/leaks.json:
  {"queue": [{"title": "BALLON D'OR WEEK 4", "tag": "PREDICTION", "sources": ["FC Mobile Forum", "Sportsdunia"],
              "groups": [{"name": "DRAFT A", "cards": [{"player": "<renderz.app/player/... of any older card>",
                          "ovr": 124, "pos": "CAM", "bg": "<renderz.app/player/... of a card from the new event>"}]}]}]}

    python -m fmm.leaks make    -> (PC) build cards + post image for every queued item
"""
import datetime as dt, json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "content" / "leaks.json"
CARDS = ROOT / "assets" / "cards" / "leaks"
HOUR = 11  # BDT: between the 07:00 Reel and the 13:00 photo


def key(it):
    return re.sub(r"[^a-z0-9]+", "_", (it["title"] + "_" + "_".join(g["name"] for g in it["groups"])).lower()).strip("_")


def card_page(url):
    from fmm import renderz
    page = renderz.fetch(url).decode("utf-8", "ignore")
    return renderz.slim(renderz.extract_array(page, "data:{player:{"))


def make_card(c):
    """Leaked card image: render of c['player'], background + text layout of c['bg'], leaked OVR/position."""
    from fmm import renderz
    pl, bg = card_page(c["player"]), card_page(c["bg"])
    out = CARDS / f"{re.sub(r'[^a-z0-9]+', '_', pl['name'].lower())}_{c['ovr']}{c['pos'].lower()}.png"
    if not out.exists():
        CARDS.mkdir(parents=True, exist_ok=True)
        renderz.build_card({**bg, "img_player": pl["img_player"], "name": c.get("name") or pl["name"],
                            "ovr": c["ovr"], "pos": c["pos"]}).save(out)
    return out, c.get("name") or pl["name"]


def render(it, cards):
    """1080x1350: title, LEAK/PREDICTION tag, each group as a labelled row of cards, sources line."""
    from fmm import atb
    from fmm.brand import base, fit_card, font, label_font, footer, W, RED, WHITE, GOLD, GRAY
    img, d, _ = base("news")
    d.text((W // 2 + 60, 150), it["title"].upper(), font=font("Anton-Regular.ttf", 78), fill=WHITE, anchor="mt")
    tag = it.get("tag", "LEAK").upper()
    tw = d.textlength(tag, font=label_font(40))
    d.rounded_rectangle((W // 2 - tw / 2 - 30, 248, W // 2 + tw / 2 + 30, 306), 29, fill=RED)
    d.text((W // 2, 277), tag, font=label_font(40), fill=WHITE, anchor="mm")
    rows = len(cards)
    d.text((W // 2, 335), "Sources: " + ", ".join(it["sources"]), font=label_font(24), fill=GRAY, anchor="mt")
    row_h = (1250 - 380) // rows
    for r, (gname, cs) in enumerate(cards):
        y0 = 380 + r * row_h
        d.text((W // 2, y0 + 4), gname.upper(), font=font("Anton-Regular.ttf", 48), fill=GOLD, anchor="mt")
        n = len(cs)
        ch = row_h - 70
        cw = min(int(ch * 0.85), (W - 80) // n - 20)
        gap = (W - n * cw) // (n + 1)
        for i, (path, _) in enumerate(cs):
            cd = fit_card(str(path), cw, ch)
            img.paste(cd, (gap + i * (cw + gap) - 30, y0 + 62 - 30), cd)
    d = ImageDraw.Draw(img)
    footer(d, "NOT OFFICIAL UNTIL EA CONFIRMS")
    img = atb.add_badge(img, key(it))  # owner rule: ATB on every photo post
    out = CARDS / f"post_{key(it)}.png"
    img.convert("RGB").save(out, quality=95)
    return out


def caption(it, cards):
    if it.get("caption"):
        return it["caption"]
    lines = "\n".join(f"{g}: " + ", ".join(n for _, n in cs) for g, cs in cards)
    return (f"🚨 {it['title']} {it.get('tag', 'LEAK').lower()}s 👀\n\n{lines}\n\n"
            f"Not official until EA confirms. Sources: {', '.join(it['sources'])}\n\n"
            "Which one are you saving for? 👇\n\n#FCMobile #FIFAMobile #EAFC #FCMobileLeaks #FMM")


def items():
    return json.loads(QUEUE.read_text(encoding="utf-8")).get("queue", []) if QUEUE.exists() else []


def make():
    """PC: build cards and post image for queued items; writes the card names into the item for the caption."""
    for it in items():
        assert len(it.get("sources", [])) >= 2, f"{it['title']}: owner rule needs 2 sources"
        cards = [(g["name"], [make_card(c) for c in g["cards"]]) for g in it["groups"]]
        print("made", render(it, cards))
        (CARDS / f"post_{key(it)}.txt").write_text(caption(it, cards), encoding="utf-8")


def post_due():
    """Cloud: next made leak post, once a day from 11:00 BDT."""
    from fmm import poster, slots
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=6)))
    if now.hour < HOUR:
        return None
    st = slots.load_state()
    done = st.setdefault("leaks_done", {})
    if now.date().isoformat() in done.values():
        return None
    for it in items():
        img, cap = CARDS / f"post_{key(it)}.png", CARDS / f"post_{key(it)}.txt"
        if key(it) in done or not img.exists() or len(it.get("sources", [])) < 2:
            continue
        res = poster.post("photo", img, cap.read_text(encoding="utf-8"), "both", "leak")  # photo + its Reel
        st = slots.load_state()
        st.setdefault("leaks_done", {})[key(it)] = now.date().isoformat()
        slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
        return res
    return None


if __name__ == "__main__":
    if sys.argv[1:2] == ["make"]:
        make()
