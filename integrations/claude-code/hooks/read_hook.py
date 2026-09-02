#!/usr/bin/env python3
"""PreToolUse hook (matcher: Read). Opt-in guard for very large files.

When Claude tries to Read a whole file bigger than TOKPACK_READ_MAX_KB
(default 64 KB, roughly 16k tokens) without offset/limit, deny once with a
reason that points at `tokpack -l 3` for an outline. Ranged reads always pass.
"""
import json
import os
import sys


def main() -> int:
    if os.environ.get("TOKPACK_HOOK_DISABLE"):
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Read":
        return 0
    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    if not path or ti.get("offset") or ti.get("limit"):
        return 0
    if path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ipynb", ".webp")):
        return 0
    try:
        size = os.path.getsize(path)
    except OSError:
        return 0
    max_kb = int(os.environ.get("TOKPACK_READ_MAX_KB", "64"))
    if size <= max_kb * 1024:
        return 0
    approx = size // 4
    reason = (
        f"{path} is {size // 1024} KB (~{approx:,} tokens). Get an outline first with "
        f"`tokpack {path} -l 3`, then Read only the ranges you need with offset/limit. "
        f"For a lossless but tighter full read use `tokpack {path} -l 1`."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
