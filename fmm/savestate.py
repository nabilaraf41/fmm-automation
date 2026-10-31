"""Save cloud/PC state to the repo without ever losing it: merge with whatever was pushed meanwhile.

    python -m fmm.savestate "message"
Snapshot content/ JSON files -> fetch + reset to origin/main -> deep-merge snapshot into the latest files
(dicts: union, lists: union, values: ours) -> commit -> push. Retries 4 times on a push race.
"""
import json, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["content/posted.json", "content/codes_state.json", "content/featured.json", "content/clips_state.json",
         "content/players_db.json", "content/card_library.json", "content/trends.json"]


def git(*a, check=True):
    r = subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a)}: {r.stderr.strip()[:300]}")
    return r


def merge(theirs, ours):
    if isinstance(theirs, dict) and isinstance(ours, dict):
        out = dict(theirs)
        for k, v in ours.items():
            out[k] = merge(theirs[k], v) if k in theirs else v
        return out
    if isinstance(theirs, list) and isinstance(ours, list):
        seen = {json.dumps(x, sort_keys=True) for x in theirs}
        return theirs + [x for x in ours if json.dumps(x, sort_keys=True) not in seen]
    return ours


def save(message):
    snap = {f: json.loads((ROOT / f).read_text(encoding="utf-8")) for f in FILES if (ROOT / f).exists()}
    binaries = git("ls-files", "--others", "--modified", "--exclude-standard", "assets/cards/rz", "content").stdout.split()
    keep = {b: (ROOT / b).read_bytes() for b in binaries if not b.endswith(".json") and (ROOT / b).exists()}
    git("fetch", "-q", "origin", "main")
    ahead = git("rev-list", "--reverse", "origin/main..HEAD").stdout.split()  # local code commits: keep them
    for attempt in range(4):
        git("fetch", "-q", "origin", "main")
        git("reset", "-q", "--hard", "origin/main")
        for c in ahead:
            git("cherry-pick", "-X", "theirs", c)
        for f, ours in snap.items():
            p = ROOT / f
            theirs = json.loads(p.read_text(encoding="utf-8")) if p.exists() else type(ours)()
            p.write_text(json.dumps(merge(theirs, ours), indent=1, ensure_ascii=False), encoding="utf-8")
        for b, data in keep.items():
            (ROOT / b).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / b).write_bytes(data)
        git("add", "-A", "content", "assets/cards/rz")
        if git("diff", "--cached", "--quiet", check=False).returncode == 0:
            if not ahead:
                print("state: nothing new"); return
        else:
            git("commit", "-q", "-m", message)
        if git("push", "-q", "origin", "HEAD:main", check=False).returncode == 0:
            print("state saved"); return
        time.sleep(3 + attempt * 3)
    raise RuntimeError("state save: push kept failing")


if __name__ == "__main__":
    assert merge({"a": 1, "l": [1]}, {"b": 2, "l": [1, 2]}) == {"a": 1, "b": 2, "l": [1, 2]}
    assert merge({"seen": {"X": 1}}, {"seen": {"Y": 2}}) == {"seen": {"X": 1, "Y": 2}}
    save(sys.argv[1] if len(sys.argv) > 1 else "Update state [skip ci]")
