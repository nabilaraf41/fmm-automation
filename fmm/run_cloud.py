"""One scheduled run: check for new redeem codes, make posts, publish today's queue.

Used by .github/workflows/codes.yml every 3 hours. Safe to run any number of times:
codes_state.json and posted.json stop anything being made or posted twice.
"""
import datetime as dt
from fmm import codes, poster

if __name__ == "__main__":
    try:  # new-player drops (Thursday 07:00 BDT, or any surprise batch) -> extra posts
        from fmm import newplayers
        newplayers.run()
    except Exception as ex:
        print("new-player check skipped:", str(ex)[:150])
    codes.run()
    today = codes.QUEUE / dt.date.today().isoformat()
    if today.exists():
        poster.run_queue(today, "both")
    else:
        print("nothing new to post")
