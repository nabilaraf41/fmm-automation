"""'WHICH ONE is the best attack?' (owner 21 Nov, menacesoccerhq style): 3 rows = 3 clubs, each its best ST/LW/RW
FC Mobile cards; viewers comment 1, 2 or 3. Photo + Reel, Saturday 13:00."""
import datetime as dt
from pathlib import Path
from PIL import Image, ImageDraw

from fmm import brand

ATTACK = ("ST", "CF", "LW", "RW", "LF", "RF")
SKIP = {"Icons", "Heroes", "Classics", "None", ""}
ROWS = [(214, 40, 90), (230, 170, 20), (200, 30, 40)]  # pink, gold, red like the reference


# famous real attacks (club, trio) -> each player's best FC Mobile card on FC Mobile Forum; 3 rows per post, rotates weekly
TRIOS = [("BARCELONA MSN", ["Messi", "Suárez", "Neymar Jr"]), ("ARSENAL 2004", ["Henry", "Bergkamp", "Pires"]),
         ("REAL MADRID 2002", ["Luís Figo", "Raúl", "Ronaldo"]), ("INTER 2010", ["Milito", "Eto'o", "Sneijder"]),
         ("BARCELONA NOW", ["Lamine Yamal", "Raphinha", "Lewandowski"]), ("JUVENTUS", ["Del Piero", "Trezeguet", "Nedvěd"]),
         ("REAL MADRID NOW", ["Mbappé", "Vini Jr.", "Bellingham"]), ("AC MILAN 1990", ["van Basten", "Gullit", "Rijkaard"]),
         ("MAN UNITED 2008", ["Rooney", "Tévez", "Owen"]), ("BRAZIL 2002", ["Ronaldo", "Rivaldo", "Ronaldinho"]),
         ("CHELSEA", ["Drogba", "Lampard", "Hazard"]), ("BAYERN", ["Ribéry", "Lewandowski", "Musiala"]),
         ("FRANCE 1998", ["Zidane", "Henry", "Trezeguet"]), ("MAN CITY", ["Haaland", "Foden", "De Bruyne"]),
         ("BARCELONA 2006", ["Ronaldinho", "Eto'o", "Messi"]), ("ITALY", ["Baggio", "Totti", "Del Piero"]),
         ("LIVERPOOL 2014", ["Suárez", "Sturridge", "Gerrard"]), ("GERMANY 2014", ["Müller", "Klose", "Götze"]),
         ("PSG", ["Mbappé", "Neymar Jr", "Messi"]), ("SPAIN 2010", ["Torres", "Iniesta", "Xavi"]),
         ("AC MILAN 2007", ["Kaká", "Shevchenko", "Ibrahimović"]), ("ARGENTINA", ["Messi", "Agüero", "Di María"]),
         ("BARCELONA 1994", ["Stoichkov", "Laudrup", "Kluivert"]), ("AFRICA LEGENDS", ["Drogba", "Eto'o", "Weah"]),
         ("PORTUGAL", ["Eusébio", "Luís Figo", "Rui Costa"]), ("ENGLAND", ["Kane", "Saka", "Owen"]),
         ("SERIE A LEGENDS", ["Batistuta", "Totti", "Baggio"]), ("GOAT TRIO", ["Pelé", "Maradona", "Cruyff"]),
         ("REAL MADRID 2000s", ["Raúl", "Morientes", "Guti"]), ("BRAZIL LEGENDS", ["Pelé", "Garrincha", "Ronaldinho"])]


def card_for(name, cards):
    """Best-OVR Forum card for this exact name, built as a png (FC Mobile Forum art) -> player dict or None."""
    from fmm import shards, fmf, renderz
    m = [c for c in cards if shards.norm(c["player_name"]) == shards.norm(name)]
    if not m:
        return None
    c = max(m, key=lambda c: c["ovr"]); art = c.get("card") or {}
    p = {"id": f"s{c['id']}", "name": c["player_name"], "ovr": c["ovr"], "pos": c["position"],
         "img_player": art.get("playerImage") or c.get("player_card"), "img_bg": art.get("cardArtBackgroundUrl"),
         "layout": {}, "colors": {}}
    path = renderz.CARDS / f"{p['id']}.png"
    try:
        if not path.exists():
            fmf.build_card(p).save(path)
    except Exception:
        return None
    p["card"] = str(path)
    return p


def render(rows, out, title="WHICH ONE", sub="I S   T H E   B E S T   A T T A C K ?"):
    W, H = 1080, 1350
    img, d, _ = brand.base("event", None, (W, H))
    img = img.convert("RGBA"); d = ImageDraw.Draw(img)
    d.text((W / 2, 215), title, font=brand.font("Anton-Regular.ttf", 140), fill=(200, 255, 0), anchor="mm")
    d.text((W / 2, 310), sub, font=brand.label_font(34), fill=(255, 255, 255), anchor="mm")
    for i, (club, cards) in enumerate(rows):
        y0 = 340 + i * 305 + (70 if len(rows) == 2 else 0)
        col = ROWS[i]
        layer = Image.new("RGBA", (W, H)); ld = ImageDraw.Draw(layer)
        ld.rounded_rectangle((40, y0 + 40, W - 40, y0 + 290), 50, fill=col + (150,), outline=col + (255,), width=5)
        img.alpha_composite(layer)
        for j, p in enumerate(cards):
            c = brand.fit_card(str(p["card"]), 230, 300)
            img.alpha_composite(c, (int(330 + j * 205 - c.width / 2), y0 + 15))
        d.ellipse((65, y0 + 120, 155, y0 + 210), fill=(15, 15, 15), outline=(255, 255, 255), width=4)
        d.text((110, y0 + 165), str(i + 1), font=brand.font("Anton-Regular.ttf", 60), fill=(255, 255, 255), anchor="mm")
        words, lines = club.split(), []
        for w in words:
            lines[-1:] = [lines[-1] + " " + w] if lines and len(lines[-1] + w) < 9 else lines[-1:] + [w]
        f = brand.font("Anton-Regular.ttf", 40)
        for k, ln in enumerate(lines):
            d.text((935, y0 + 165 + (k - (len(lines) - 1) / 2) * 50), ln, font=f, fill=(255, 255, 255), anchor="mm")
    d.text((W / 2, H - 28), ("COMMENT 1 OR 2" if len(rows) == 2 else "COMMENT 1, 2 OR 3"), font=brand.font("Anton-Regular.ttf", 40), fill=(200, 255, 0), anchor="mm")
    img.convert("RGB").save(out, quality=94)
    return out


def post_no(day):
    """Wed + Sat posts counted from Wed 25 Nov 2026 (0, 1, 2 ...), so all 30 trios run before any repeat."""
    return ((day - dt.date(2026, 11, 25)).days // 7) * 2 + (1 if day.weekday() == 5 else 0)


def build(outdir, week=None):
    from fmm import shards
    cards = shards.forum_cards()
    w = week if week is not None else post_no(dt.date.today())
    order = TRIOS[(w * 3) % len(TRIOS):] + TRIOS[:(w * 3) % len(TRIOS)]
    rows = []
    for club, names in order:
        if set(names) & {p["name"] for _, cs in rows for p in cs}:
            continue  # one player once per post
        got = [card_for(n, cards) for n in names]
        if all(got):
            rows.append((club, got))
        if len(rows) == 3:
            break
    if len(rows) < 3:
        return None, None
    out = render(rows, Path(outdir) / "attacks.png")
    slides = [out] + [row_slide(f"OPTION {i}", club, cs, Path(outdir) / f"attacks_{i}.png",
                                labels=[f"{p['ovr']} {p['pos']}" for p in cs]) for i, (club, cs) in enumerate(rows, 1)]
    (Path(outdir) / "carousel.json").write_text(__import__("json").dumps([f.name for f in slides]), encoding="utf-8")
    cap = ("WHICH ONE is the best attack? 🤯🔥\n\n" +
           "\n".join(f"{i}. {c}: " + ", ".join(f"{p['ovr']} {p['name']}" for p in cs) for i, (c, cs) in enumerate(rows, 1)) +
           "\n\nComment 1, 2 or 3 👇\n\nCards: FC Mobile Forum.\n\n#FCMobile #FIFAMobile #EAFC #FCMobileCards #FMM")
    return out, cap


def row_slide(title, sub, cards, out, color=(200, 255, 0), labels=None):
    """Carousel slide: one row of cards, big (22 Nov upgrade: carousels get 5-10x our other posts)."""
    W, H = 1080, 1350
    img, d, _ = brand.base("event", None, (W, H))
    img = img.convert("RGBA"); d = ImageDraw.Draw(img)
    d.text((W / 2, 215), title, font=brand.font("Anton-Regular.ttf", 110), fill=color, anchor="mm")
    d.text((W / 2, 310), sub, font=brand.label_font(34), fill=(255, 255, 255), anchor="mm")
    n = len(cards)
    cols = 2 if n == 4 else n
    w, h = 1000 // cols, (340 if n == 4 else 560)
    for j, p in enumerate(cards):
        c = brand.fit_card(p["card"], w + 40, h)
        cx = 40 + w * (j % cols) + w / 2
        y = 360 + (j // cols) * (h + 115) + (60 if n < 4 else 0)
        img.alpha_composite(c, (int(cx - c.width / 2), int(y)))
        if labels:
            d.text((cx, y + c.height + 25), labels[j], font=brand.font("Anton-Regular.ttf", 44), fill=(255, 215, 0), anchor="mm")
    d.text((W / 2, H - 35), "SWIPE  •  COMMENT YOUR PICK", font=brand.label_font(28), fill=(200, 200, 200), anchor="mm")
    img.convert("RGB").save(out, quality=94)
    return out


# Sunday 17:00 "Legends vs Legends" (owner 22 Nov upgrade; FC Beast "Madrid Legends VS Barca Legends" 4.5M)
VS = [("REAL MADRID 2002", "BARCELONA 2006"), ("AC MILAN 1990", "INTER 2010"), ("BRAZIL 2002", "FRANCE 1998"),
      ("ARSENAL 2004", "MAN UNITED 2008"), ("ITALY", "GERMANY 2014"), ("BARCELONA MSN", "PSG"),
      ("JUVENTUS", "AC MILAN 2007"), ("REAL MADRID NOW", "BARCELONA NOW"), ("ARGENTINA", "PORTUGAL"),
      ("CHELSEA", "LIVERPOOL 2014"), ("MAN CITY", "BAYERN"), ("GOAT TRIO", "BRAZIL LEGENDS")]


def build_vs(outdir, n=None):
    from fmm import shards
    cards, trio = shards.forum_cards(), dict(TRIOS)
    n = n if n is not None else (dt.date.today() - dt.date(2026, 11, 29)).days // 7
    for k in range(len(VS)):
        a, b = VS[(n + k) % len(VS)]
        rows = [(c, [card_for(x, cards) for x in trio[c]]) for c in (a, b)]
        if all(all(cs) for _, cs in rows):
            break
    else:
        return None, None
    out = render(rows, Path(outdir) / "legends.png", title="WHO WINS?", sub="1   O R   2 ?")
    cap = (f"{a} vs {b}: who wins? ⚔️🔥\n\n" +
           "\n".join(f"{i}. {c}: " + ", ".join(f"{p['ovr']} {p['name']}" for p in cs) for i, (c, cs) in enumerate(rows, 1)) +
           "\n\nComment 1 or 2 👇\n\nCards: FC Mobile Forum.\n\n#FCMobile #FIFAMobile #EAFC #FCMobileCards #FMM")
    return out, cap
