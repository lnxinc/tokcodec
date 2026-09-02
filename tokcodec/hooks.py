"""Claude Code PreToolUse hooks, exposed as `tokcodec hook bash` and `tokcodec hook read`.

Both read the hook JSON on stdin and print a JSON decision (or nothing).
Both FAIL OPEN: any error, or tokcodec missing from PATH, means "do nothing"
and the user's command runs exactly as Claude wrote it.

Knobs: TOKCODEC_HOOK_LEVEL (default 3), TOKCODEC_READ_MAX_KB (default 64),
TOKCODEC_HOOK_DISABLE=1 turns both off.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys

NOISY = re.compile(
    r"^(?:\S+=\S+\s+)*"            # leading VAR=value
    r"(?:cd\s+\S+\s*&&\s*)?"      # optional cd
    r"(?:"
    r"(?:npm|pnpm|yarn|bun)\s+(?:install|i|ci|test|run\s+\S+|build)\b"
    r"|(?:python3?\s+-m\s+)?pytest\b"
    r"|(?:uv\s+run\s+)?pytest\b"
    r"|cargo\s+(?:build|test|check|clippy)\b"
    r"|go\s+(?:test|build|vet)\b"
    r"|make\b"
    r"|mvn\b|gradle\b|\./gradlew\b"
    r"|docker\s+(?:build|compose)\b"
    r"|git\s+(?:pull|push|fetch|clone)\b"
    r"|pip3?\s+install\b|uv\s+(?:sync|pip)\b"
    r"|tsc\b|eslint\b|ruff\b|mypy\b"
    r")"
)

# Output is captured to a temp file first, so if tokcodec is missing or crashes
# the raw output is still shown (`|| cat`) and the command's own exit code is
# what Claude sees (`(exit $rc)` sets $? without killing the shell).
WRAP = (
    '__t=$(mktemp); {{ {cmd}; }} >"$__t" 2>&1; __rc=$?; '
    '{{ tokcodec "$__t" -k log -l {level} 2>/dev/null || cat "$__t"; }}; '
    'rm -f "$__t"; (exit $__rc)'
)


def _load() -> dict | None:
    if os.environ.get("TOKCODEC_HOOK_DISABLE"):
        return None
    try:
        return json.load(sys.stdin)
    except Exception:
        return None


def bash_decision(data: dict) -> dict | None:
    if data.get("tool_name") != "Bash":
        return None
    ti = data.get("tool_input") or {}
    cmd = (ti.get("command") or "").strip()
    if not cmd or ti.get("run_in_background"):
        return None
    if "tokcodec" in cmd or "# raw" in cmd or "|" in cmd or ">" in cmd or "\n" in cmd:
        return None
    if not NOISY.match(cmd):
        return None
    if shutil.which("tokcodec") is None:
        return None  # fail open: nothing to pipe through
    level = os.environ.get("TOKCODEC_HOOK_LEVEL", "3")
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "updatedInput": {"command": WRAP.format(cmd=cmd, level=level)}}}


def read_decision(data: dict) -> dict | None:
    if data.get("tool_name") != "Read":
        return None
    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    if not path or ti.get("offset") or ti.get("limit"):
        return None
    if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ipynb", ".webp")):
        return None
    try:
        size = os.path.getsize(path)
    except OSError:
        return None
    max_kb = int(os.environ.get("TOKCODEC_READ_MAX_KB", "64"))
    if size <= max_kb * 1024:
        return None
    reason = (
        f"{path} is {size // 1024} KB (~{size // 4:,} tokens). Get an outline first with "
        f"`tokcodec {path} -l 3`, then Read only the ranges you need with offset/limit. "
        f"For a lossless but tighter full read use `tokcodec {path} -l 1`."
    )
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny", "permissionDecisionReason": reason}}


def run(which: str) -> int:
    try:
        data = _load()
        if data is None:
            return 0
        out = bash_decision(data) if which == "bash" else read_decision(data)
        if out:
            print(json.dumps(out))
    except Exception:
        pass  # fail open
    return 0
