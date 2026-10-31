"""Weekly Top 10 per position from fcmobileforum.com/top-20/<pos> (updated every week by the site).

Each ranked card is cross-checked: it must exist in the RenderZ card library (same card id) or its program
must be confirmed; unconfirmed cards are skipped and the next ranked card moves up.

    python -m fmm.top20 st      -> print the confirmed Top 10 STs
"""
import json, re, sys
from fmm import fmf, renderz

POSITIONS = ["st", "lw", "rw", "cam", "cm", "cdm", "lb", "cb", "rb", "gk", "lm", "rm"]


def ranking(pos):
    t = fmf.flight_text(fmf.fetch(f"https://fcmobileforum.com/top-20/{pos}").decode("utf-8", "ignore"))
    i = t.find('"initialPlayers":[')
    if i < 0:
        raise RuntimeError("top-20 layout changed")
    return fmf.initial_players(t[i - 1:].replace('"initialPlayers":', '"initialPlayers":', 1)) \
        if False else _arr(t, i + len('"initialPlayers":'))


def _arr(t, i):
    depth, in_str, j = 0, False, i
    while j < len(t):
        c = t[j]
        if in_str:
            if c == "\\": j += 2; continue
            if c == '"': in_str = False
        elif c == '"': in_str = True
        elif c in "[{": depth += 1
        elif c in "]}":
            depth -= 1
            if depth == 0:
                return json.loads(t[i:j + 1])
        j += 1
    raise RuntimeError("unterminated list")


def program_of(image_url):
    m = re.search(r"/\d+_([A-Z]+\d*)_", image_url or "")
    return m.group(1) if m else ""


def top10(pos, confirmed=None):
    """Confirmed Top 10 for a position -> list of player dicts (with 'card' path when an image exists)."""
    from fmm import versions, slots
    lib = versions.library()
    st = slots.load_state()
    ok_progs = set(st.get("confirmed_programs", [])) | set(confirmed or [])
    out = []
    for x in sorted(ranking(pos), key=lambda x: x.get("rank", 99)):
        card = lib.get(str(x.get("cardId")))
        prog = program_of(x.get("image"))
        if (not card and prog not in ok_progs) or not (card or {}).get("ovr"):
            continue  # cross-check failed / incomplete: skip
        p = dict(card or {})
        p.update(name=x["name"], pos=x["position"], rank=x["rank"], program=p.get("program") or prog,
                 id=str(x.get("cardId")), render=x.get("image"))
        path = renderz.CARDS / f"{p['id']}.png"
        p["card"] = str(path) if path.exists() else None
        out.append(p)
        if len(out) == 10:
            break
    return out


def ensure_images(players):
    """Card image for each player: existing RenderZ-built card, else an FMM frame around the forum render."""
    import io
    from PIL import Image
    from fmm.brand import player_card
    for p in players:
        if p.get("card"):
            continue
        path = renderz.CARDS / f"{p['id']}.png"
        try:
            ren = renderz.CARDS / f"{p['id']}_render.png"
            Image.open(io.BytesIO(fmf.fetch(p["render"]))).convert("RGBA").save(ren)
            player_card({"name": p["name"], "ovr": p.get("ovr") or "", "pos": p["pos"], "image": str(ren),
                         "tier": "gold"}, 512, 716).save(path)
            ren.unlink(missing_ok=True)
            p["card"] = str(path)
        except Exception as ex:
            print("image skipped", p["name"], str(ex)[:60])
    return [p for p in players if p.get("card")]


if __name__ == "__main__":
    for p in top10(sys.argv[1] if len(sys.argv) > 1 else "st"):
        print(p["rank"], p.get("ovr"), p["name"], p["program"], "card" if p["card"] else "no image yet")
