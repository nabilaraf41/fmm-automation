"""Custom FMM cards (owner 16 Nov): any player render or local cutout on any event background, any OVR/pos/name,
always stamped "FMM CONCEPT" so nobody mistakes them for real game cards.
    card(bg_page, ovr, pos, name, player=<renderz page URL | local png>, out=Path) -> Path
"""
import io
from pathlib import Path
from PIL import Image, ImageDraw

from fmm import renderz
from fmm.brand import title_font

BALLON = "https://renderz.app/player/30922860"   # Ballon d'Or event background (same as the leak posts)


def _page(url):
    from fmm.leaks import card_page
    return card_page(url)


def card(bg_page, ovr, pos, name, player=None, out=None, size=1024, stamp="FMM CONCEPT"):
    bg = _page(bg_page)
    pl = {**bg, "ovr": ovr, "pos": pos, "name": name, "img_player": None}
    if player and str(player).startswith("http"):
        pl["img_player"] = _page(player)["img_player"]
    img = renderz.build_card(pl, size=size).convert("RGBA")  # background + text, no render yet
    if player and not str(player).startswith("http"):     # local cutout (e.g. ATB): fit into the card's picture area
        cut = Image.open(player).convert("RGBA")
        cut = cut.crop(cut.getbbox())
        h = int(img.height * 0.62)
        cut = cut.resize((int(cut.width * h / cut.height), h), Image.LANCZOS)
        if cut.width > img.width * 0.8:
            cut = cut.crop(((cut.width - int(img.width * 0.8)) // 2, 0, (cut.width + int(img.width * 0.8)) // 2, h))
        layer = Image.new("RGBA", img.size)
        layer.alpha_composite(cut, ((img.width - cut.width) // 2, int(img.height * 0.66) - h))
        img = _under_text(img, layer, pl, size)
    if stamp:
        d = ImageDraw.Draw(img)
        f = title_font(int(img.width * 0.045))
        w = d.textlength(stamp, font=f)
        y = img.height - int(img.height * 0.075)
        d.rounded_rectangle(((img.width - w) / 2 - 18, y - 6, (img.width + w) / 2 + 18, y + f.size + 10), 14,
                            fill=(0, 0, 0, 190))
        d.text((img.width / 2, y), stamp, font=f, fill=(255, 215, 0), anchor="ma")
    out = Path(out or renderz.CARDS / f"concept_{name.lower().replace(' ', '_')}_{ovr}.png")
    img.save(out)
    return out


def _under_text(img, layer, pl, size):
    """Put the cutout above the background but under the OVR/pos/name text: rebuild text on top."""
    base = renderz.build_card({**pl, "img_player": None, "ovr": "", "pos": "", "name": ""}, size=size).convert("RGBA")
    base = base.resize(img.size)
    base.alpha_composite(layer)
    text_only = renderz.build_card({**pl, "img_player": None}, size=size).convert("RGBA").resize(img.size)
    # text pixels = where text_only differs from the empty card
    empty = renderz.build_card({**pl, "img_player": None, "ovr": "", "pos": "", "name": ""}, size=size).convert("RGBA").resize(img.size)
    from PIL import ImageChops
    mask = ImageChops.difference(text_only.convert("RGB"), empty.convert("RGB")).convert("L").point(lambda v: 255 if v > 30 else 0)
    base.paste(text_only, (0, 0), mask)
    return base
