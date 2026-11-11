"""Phone alerts through ntfy.sh (free, no account): owner installs the ntfy app and subscribes to TOPIC.
python -m fmm.notify "title" "message"   |   python -m fmm.notify --log run.log  (alert if the run log shows a failure)
"""
import re, sys
import requests

TOPIC = "fmm-atb-d3e1ffff27"  # random name = only the owner knows it (ntfy topics are public by name)
BAD = re.compile(r"slot failed|all platforms failed|Traceback|long video skipped|OAuthException|token.*(expired|invalid)", re.I)


def send(title, msg, tags="soccer", click=None):
    try:
        h = {"Title": title.encode("utf-8"), "Tags": tags}
        if click:
            h["Click"] = click
        requests.post(f"https://ntfy.sh/{TOPIC}", data=msg.encode("utf-8"), headers=h, timeout=20)
    except Exception as ex:  # an alert never breaks a run
        print("notify skipped:", str(ex)[:100])


def check_log(path):
    lines = [l.strip() for l in open(path, encoding="utf-8", errors="ignore") if BAD.search(l)]
    if lines:
        send("⚠️ FMM bot problem", "\n".join(lines[:5])[:1500], tags="warning")
    return lines


if __name__ == "__main__":
    if sys.argv[1:2] == ["--log"]:
        check_log(sys.argv[2])
    else:
        send(sys.argv[1], sys.argv[2])
