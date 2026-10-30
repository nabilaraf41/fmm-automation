"""PC-side collector (RenderZ blocks cloud servers, so this runs on the home PC when it's on).

Fetches new cards from RenderZ, builds card images for the latest players, then commits and pushes
players_db.json + assets/cards/rz/ so the cloud slots can use them.

    python -m fmm.collect
"""
import subprocess
from pathlib import Path
from fmm import renderz, slots

ROOT = Path(__file__).resolve().parent.parent


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)


if __name__ == "__main__":
    git("pull", "--rebase", "-q")
    fresh, db, made = slots.latest_players()
    built = 0
    for p in list(fresh.values())[:24]:  # make sure every recent card has an image
        if slots.ensure_card(p, fresh):
            built += 1
    git("add", "content/players_db.json", "assets/cards/rz")
    if git("diff", "--cached", "--quiet").returncode:
        git("-c", "user.name=fmm-pc", "-c", "user.email=fmm-pc@users.noreply.github.com",
            "commit", "-q", "-m", f"Collect cards from RenderZ ({len(made)} new) [skip ci]")
        print(git("push", "-q").stderr or "pushed")
    print(f"new: {len(made)} | cards ready: {built}")
