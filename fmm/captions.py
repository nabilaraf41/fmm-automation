"""Polish every caption before it posts (rules from github.com/Jakeschincariol/instagram-agent-skill, MIT):
- humanizer: strip em dashes, AI-slop words and invisible characters (vendor/humanize.py + slop.json)
- line 1 is what the feed shows before "... more": never starts with an emoji, kept under 125 characters
- at most 5 hashtags, on their own last line
"""
import re
from fmm.vendor import humanize as H

_LEX = H.load_lexicon()
EMOJI_START = re.compile(r"^[^\w#@\"'(]+\s*")  # leading emoji/symbols on line 1


def polish(caption):
    text, _ = H.humanize(caption, _LEX)
    lines = text.strip().split("\n")
    first = lines[0]
    lead = EMOJI_START.match(first)
    if lead and lead.group(0).strip():
        first = first[lead.end():] + " " + lead.group(0).strip()  # move the emoji to the end of the hook
    if len(first) > 125:
        first = first[:122].rsplit(" ", 1)[0] + "..."
    lines[0] = first
    tags = [w for l in lines for w in l.split() if w.startswith("#")]
    body = [l for l in lines[1:] if not (l.strip() and all(w.startswith("#") for w in l.split()))]
    out = "\n".join([lines[0]] + body).rstrip()
    if tags:
        tags = list(dict.fromkeys(tags))
        keep = tags[:5] if "#FMM" in tags[:5] or "#FMM" not in tags else tags[:4] + ["#FMM"]  # brand tag always stays
        out += "\n\n" + " ".join(keep)
    return out


if __name__ == "__main__":
    s = polish("🔥 Is 124 OVR Kane worth it? — let's dive in\n\nHe is a game-changer.\n\n#FCMobile #FIFAMobile #EAFC #PlayerReview #Kane #FMM")
    print(s)
    assert not s[0] in "🔥" and s.count("#") <= 5 and "—" not in s and "#FMM" in s
