"""ATB Meme: ATB says NO (top) / YES (bottom) on the left, two things on the right (owner's template).

The owner tells Claude what goes on the right; Claude adds it to content/atb_meme.json:
    {"queue": [{"top": "C. Ronaldo 124 LW", "bottom": "C. Ronaldo 118 ST", "label": "EA", "caption": "..."}]}
top/bottom: a card ("Name OVR [POS]", must be a confirmed card), "img:<file>" from assets/atb_meme/items/,
or plain text. label (optional) goes on ATB's panels, like "EA". caption is optional.
The cloud posts the next queued meme once a day at 15:00 BDT (photo + its Reel with ATB, via poster.post).

    python -m fmm.atbmeme test "C. Ronaldo 124 LW" "C. Ronaldo 118 ST" EA   -> output/atb_meme_test.png
"""
import datetime as dt, json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "atb_meme"
QUEUE = ROOT / "content" / "atb_meme.json"
HOUR = 15  # BDT: between the 13:00 and 17:00 photo slots
W, H = 1080, 1350
PW, PH = W // 2, H // 2


def find_card(spec):
    """'C. Ronaldo 124 LW' -> confirmed card dict with an image path, or None."""
    from fmm import renderz, slots
    m = re.match(r"(.+?)\s+(\d{2,3})(?:\s+([A-Z]{2,3}))?$", spec.strip())
    if not m:
        return None
    name, ovr, pos = m.group(1).lower(), int(m.group(2)), m.group(3)
    db = json.loads(renderz.DB.read_text(encoding="utf-8"))["players"] if renderz.DB.exists() else {}
    try:
        fresh, _, _ = slots.latest_players()
    except Exception:
        fresh = {}
    from fmm import versions
    cands = {**versions.library(), **db, **fresh}  # card_library.json holds older versions too
    cands = slots.confirmed_only({k: v for k, v in cands.items() if (v.get("name") or "").lower().endswith(name.split()[-1])
                                  and name in (v.get("name") or "").lower() and v.get("ovr") == ovr
                                  and (not pos or v.get("pos") == pos)})
    for p in cands.values():
        path = (renderz.CARDS / f"{p['id']}.png")
        if path.exists() or slots.ensure_card(p, fresh):
            return {**p, "card": str(path)}
    return None


def _item(spec):
    """Right-side image (RGBA) for one spec, and a short name for the caption."""
    from fmm.brand import load_card, font, WHITE
    if spec.startswith("img:"):
        return Image.open(ASSETS / "items" / spec[4:]).convert("RGBA"), Path(spec[4:]).stem
    c = find_card(spec)
    if c:
        return load_card(c["card"]), f"{c['ovr']} {c.get('pos', '')} {c['name']}".replace("  ", " ")
    if re.match(r".+\s\d{2,3}(\s[A-Z]{2,3})?$", spec.strip()):  # looks like a card but isn't confirmed: never post it
        raise ValueError(f"card not found / not confirmed: {spec}")
    im = Image.new("RGBA", (PW - 60, PH - 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    from fmm.brand import wrap
    f = font("Anton-Regular.ttf", 76)
    lines = wrap(d, spec.upper(), f, PW - 80)
    y = (im.height - len(lines) * 90) // 2
    for ln in lines:
        d.text((im.width // 2, y), ln, font=f, fill=WHITE, anchor="mt", stroke_width=4, stroke_fill=(0, 0, 0)); y += 90
    return im, spec


def render(top, bottom, label=None, out=None):
    from fmm.brand import font, LOGO, WHITE
    img = Image.new("RGB", (W, H), (8, 10, 14))
    # right side: dark with a green glow (top) and a purple glow (bottom), like the reference
    glow = Image.new("RGB", (PW, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-PW * .5, -H * .15, PW * .7, H * .45), fill=(10, 140, 70))
    gd.ellipse((PW * .2, H * .45, PW * 1.5, H * 1.05), fill=(110, 30, 200))
    img.paste(Image.blend(Image.new("RGB", (PW, H), (8, 10, 14)), glow.filter(ImageFilter.GaussianBlur(120)), 0.55), (PW, 0))
    names = []
    for i, (face, spec) in enumerate([("no", top), ("yes", bottom)]):
        y0 = i * PH
        a = Image.open(ASSETS / f"{face}.jpg").convert("RGB")
        s = PH / a.height
        a = a.resize((round(a.width * s), PH), Image.LANCZOS)
        a = a.crop(((a.width - PW) // 2, 0, (a.width - PW) // 2 + PW, PH))
        img.paste(a, (0, y0))
        d = ImageDraw.Draw(img)
        if label:
            f = font("Anton-Regular.ttf", 120)
            d.text((PW - 40, y0 + PH - 70), label.upper(), font=f, fill=WHITE, anchor="rs",
                   stroke_width=6, stroke_fill=(0, 0, 0))
        it, nm = _item(spec)
        names.append(nm)
        it.thumbnail((PW - 90, PH - 90), Image.LANCZOS)
        img.paste(it, (PW + (PW - it.width) // 2, y0 + (PH - it.height) // 2), it)
    d = ImageDraw.Draw(img)
    d.line((0, PH, W, PH), fill=(0, 0, 0), width=6)
    d.line((PW, 0, PW, H), fill=(0, 0, 0), width=6)
    logo = Image.open(LOGO).convert("RGBA")
    logo.putalpha(logo.convert("L").point(lambda v: 0 if v < 40 else 255))
    logo.thumbnail((150, 75))
    img.paste(logo, (W - logo.width - 24, 20), logo)
    out = Path(out or ROOT / "output" / "atb_meme.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=95)
    return out, names


def caption(item, names):
    if item.get("caption"):
        return item["caption"]
    who = f"{item['label']} " if item.get("label") else ""
    return (f"{who}be like 🤡\n\n❌ {names[0]}\n✅ {names[1]}\n\n"
            "Which one would you pick? 👇\n\n#FCMobile #FIFAMobile #EAFC #FCMobileMemes #FMM")


def post_due():
    """Next queued meme, once a day from 15:00 BDT. Returns the post ids or None."""
    from fmm import poster, slots
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=6)))
    if now.hour < HOUR or not QUEUE.exists():
        return None
    st = slots.load_state()
    done = st.setdefault("atb_meme_done", {})  # dict (not list): state saves merge dicts safely
    if now.date().isoformat() in done.values():
        return None
    key = lambda it: f"{it['top']}|{it['bottom']}|{it.get('label', '')}"
    todo = [it for it in json.loads(QUEUE.read_text(encoding="utf-8")).get("queue", []) if key(it) not in done]
    if not todo:
        return None
    it = todo[0]
    try:
        path, names = render(it["top"], it["bottom"], it.get("label"))
    except ValueError as ex:  # unconfirmed card: skip this one for good, tell the owner in the log
        print("atb meme skipped:", ex)
        done[key(it)] = "skipped: " + str(ex)[:60]
        slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
        return None
    res = poster.post("photo", path, caption(it, names), "both", "atb_meme")  # photo + its Reel (ATB clip on top)
    st = slots.load_state()
    st.setdefault("atb_meme_done", {})[key(it)] = now.date().isoformat()
    slots.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


if __name__ == "__main__":
    if sys.argv[1:2] == ["test"]:
        a = sys.argv[2:]
        print(render(a[0], a[1], a[2] if len(a) > 2 else None, ROOT / "output" / "atb_meme_test.png"))
