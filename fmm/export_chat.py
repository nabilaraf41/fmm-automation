"""Export a Claude Code chat to searchable text in docs/history/ (PC only, gitignored), secrets removed.

    python -m fmm.export_chat                 -> exports the newest chat of this project
    python -m fmm.export_chat <file.jsonl>    -> exports that chat
Chats live in ~/.claude/projects/E--Claude-FMM/*.jsonl
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHATS = Path.home() / ".claude" / "projects" / "E--Claude-FMM"
SECRET = (r"EAA[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|ya29\.[A-Za-z0-9_-]{20,}"
          r"|1//[A-Za-z0-9_-]{30,}|GOCSPX-[A-Za-z0-9_-]{10,}"
          r"|\"(?:refresh_token|client_secret|access_token|token)\"\s*:\s*\"[^\"]{12,}\"")


def export(src):
    src = Path(src)
    out, first, last = [], "", ""
    for line in open(src, encoding="utf-8"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        m = e.get("message") or {}
        role, ts, c = m.get("role"), (e.get("timestamp") or "")[:16], m.get("content")
        if ts:
            first, last = first or ts, ts
        for b in ([{"type": "text", "text": c}] if isinstance(c, str) else c or []):
            t = b.get("type")
            if t == "text" and b.get("text", "").strip():
                txt = b["text"]
                if role == "user" and txt.lstrip().startswith("<system-reminder>") and len(txt) > 3000:
                    continue
                out.append(f"\n## {ts} {'OWNER' if role == 'user' else 'CLAUDE'}\n{txt.strip()}\n")
            elif t == "tool_use":
                out.append(f"\n[{ts} tool {b.get('name')}] {json.dumps(b.get('input', {}), ensure_ascii=False)[:1500]}\n")
            elif t == "tool_result":
                r = b.get("content")
                if isinstance(r, list):
                    r = " ".join(x.get("text", "") for x in r if isinstance(x, dict))
                out.append(f"[result] {str(r)[:800]}\n")
    text, n = re.subn(SECRET, "[SECRET REMOVED]", "".join(out).replace("\x00", ""))
    dst = ROOT / "docs" / "history" / f"chat-{first[:10]}_to_{last[:10]}_{src.stem[:8]}.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(f"# Full text of chat {src.stem} ({first[:10]} to {last[:10]})\n" + text, encoding="utf-8")
    return dst, n


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else max(CHATS.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    dst, n = export(src)
    assert not re.search(SECRET, dst.read_text(encoding="utf-8")), "secret left in export"  # self-check
    print("saved", dst, "| secrets removed:", n)
