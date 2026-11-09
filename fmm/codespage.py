"""Public "latest FC Mobile codes" web page: the link sent by the comment -> DM automation.

The 5 newest codes from content/codes_state.json (active ones marked LIVE), each with a Copy button and the redeem
link. fmm.codes calls publish() after every check, so a new code is on the page within the same cloud run.
Hosting: GitHub Pages on a separate PUBLIC repo (env PAGES_REPO, e.g. "nabilaraf41/fmm-codes") written through the
GitHub contents API with a fine-grained token (env PAGES_TOKEN, Contents read+write on that repo only).

    python -m fmm.codespage            -> output/codes_page/index.html (local preview, nothing uploaded)
"""
import base64, html, json, os, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "content" / "codes_state.json"
OUT = ROOT / "output" / "codes_page" / "index.html"
REDEEM = "https://redeem.fcm.ea.com"


def latest(n=5, active=None):
    seen = json.loads(STATE.read_text(encoding="utf-8")).get("seen", {}) if STATE.exists() else {}
    live = {c["code"] for c in (active or [])}
    rows = sorted(seen.values(), key=lambda c: c.get("first_seen", ""), reverse=True)
    rows = sorted(rows, key=lambda c: c["code"] not in live)[:n]  # live codes first, then newest
    return [{**c, "live": c["code"] in live} for c in rows]


def page(rows, updated):
    e = html.escape
    cards = "".join(f"""
  <div class="code{' off' if not r['live'] else ''}">
    <div class="top"><span class="tag">{'LIVE' if r['live'] else 'MAY BE EXPIRED'}</span><span class="date">{e(r.get('date') or r.get('first_seen', ''))}</span></div>
    <div class="name">{e(r['code'])}</div>
    <div class="reward">{e(r.get('reward', ''))}</div>
    <button onclick="cp(this,'{e(r['code'])}')">Copy code</button>
  </div>""" for r in rows) or '<p class="none">No codes right now. Follow FMM, we post every new code first.</p>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FC Mobile Codes | FMM</title>
<meta name="description" content="Latest FC Mobile redeem codes and rewards, updated automatically by FC Mobile Mania (FMM).">
<style>
:root{{--bg:#050505;--card:#14141c;--red:#E1062C;--gold:#FFD700;--txt:#fff;--mut:#a8a8b3}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 20% 0%,#3a0b5c 0,transparent 45%),radial-gradient(circle at 90% 100%,#5c0618 0,transparent 45%),var(--bg);color:var(--txt);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;min-height:100vh}}
.wrap{{max-width:520px;margin:0 auto;padding:20px 16px 40px}}
h1{{font-size:30px;margin:8px 0 2px;letter-spacing:.5px}}h1 b{{color:var(--gold)}}
.sub{{color:var(--mut);font-size:14px;margin-bottom:18px}}
.redeem{{display:block;text-align:center;background:var(--red);color:#fff;text-decoration:none;font-weight:800;padding:14px;border-radius:14px;font-size:17px;margin-bottom:18px}}
.code{{background:var(--card);border:1.5px solid #2a2a38;border-radius:16px;padding:14px 16px;margin-bottom:12px}}
.code:not(.off){{border-color:var(--gold);box-shadow:0 0 18px #ffd70033}}
.off{{opacity:.6}}
.top{{display:flex;justify-content:space-between;font-size:12px;color:var(--mut)}}
.tag{{color:#000;background:var(--gold);padding:2px 8px;border-radius:8px;font-weight:800}}.off .tag{{background:#555;color:#fff}}
.name{{font-size:28px;font-weight:900;letter-spacing:1px;margin:8px 0 2px;word-break:break-all}}
.reward{{color:var(--mut);font-size:15px;margin-bottom:12px}}
button{{width:100%;padding:12px;border:0;border-radius:12px;background:#fff;color:#000;font-weight:800;font-size:16px;cursor:pointer}}
.how{{color:var(--mut);font-size:14px;line-height:1.5;margin-top:22px}}.how b{{color:#fff}}
.none{{color:var(--mut)}}footer{{text-align:center;color:var(--mut);font-size:12px;margin-top:24px}}
</style></head><body><div class="wrap">
<h1>FC Mobile <b>Codes</b></h1>
<div class="sub">By FC Mobile Mania (FMM) · updated {e(updated)} (Bangladesh time)</div>
<a class="redeem" href="{REDEEM}" target="_blank" rel="noopener">Redeem at redeem.fcm.ea.com</a>
{cards}
<div class="how"><b>How to redeem:</b> copy a code, open redeem.fcm.ea.com, log in with your EA account,
paste the code, then open FC Mobile and collect the reward from your inbox.</div>
<footer>Not affiliated with EA. Codes checked automatically; expired ones may stop working.</footer>
</div>
<script>function cp(b,c){{navigator.clipboard&&navigator.clipboard.writeText(c);b.textContent='Copied ✓';setTimeout(()=>b.textContent='Copy code',1500)}}</script>
</body></html>"""


def build(active=None):
    import datetime as dt
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=6)))
    text = page(latest(5, active), now.strftime("%d %b %Y, %H:%M"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    return text


def publish(active=None):
    """Write index.html to the public Pages repo when its code list changed. No env -> local file only."""
    text = build(active)
    repo, token = os.environ.get("PAGES_REPO"), os.environ.get("PAGES_TOKEN")
    if not (repo and token):
        return None
    url = f"https://api.github.com/repos/{repo}/contents/index.html"
    hdr = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "fmm-codes"}
    sha, old = None, ""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=30) as r:
            j = json.load(r)
            sha, old = j["sha"], base64.b64decode(j["content"]).decode("utf-8", "ignore")
    except Exception:
        pass  # first upload
    strip = lambda t: t.split("updated ", 1)[-1].split("</div>", 1)[-1]  # ignore the timestamp line
    if old and strip(old) == strip(text):
        return "unchanged"
    body = json.dumps({"message": "Update codes", "content": base64.b64encode(text.encode()).decode(),
                       **({"sha": sha} if sha else {})}).encode()
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdr, method="PUT"), timeout=30) as r:
        return r.status


if __name__ == "__main__":
    rows = latest(5, [{"code": "COSTUMEPARTY"}])
    assert len(rows) <= 5 and (not rows or rows[0]["code"] == "COSTUMEPARTY"), rows  # live codes listed first
    print(build([{"code": "COSTUMEPARTY"}])[:0] or f"made {OUT}")
