"""One scheduled run: check for new redeem codes, make posts, publish today's queue.

Used by .github/workflows/codes.yml every 3 hours. Safe to run any number of times:
codes_state.json and posted.json stop anything being made or posted twice.
"""
import datetime as dt
from fmm import codes, poster

if __name__ == "__main__":
    codes.run()
    today = codes.QUEUE / dt.date.today().isoformat()
    if today.exists():
        poster.run_queue(today, "both")
    else:
        print("nothing new to post")
