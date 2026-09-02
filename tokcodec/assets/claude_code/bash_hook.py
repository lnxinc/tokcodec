#!/usr/bin/env python3
"""PreToolUse hook (matcher: Bash).

Pipes noisy commands (tests, builds, installs, git fetches) through
`tokcodec - -k log -l 3` so Claude sees a compressed, failure-preserving
transcript instead of thousands of repeated lines.

Opt out for one command by including `tokcodec` or `# raw` in it.
Tune with env vars: TOKCODEC_HOOK_LEVEL (default 3), TOKCODEC_HOOK_DISABLE=1.
"""
import json
import os
import re
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


def main() -> int:
    if os.environ.get("TOKCODEC_HOOK_DISABLE"):
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    if data.get("tool_name") != "Bash":
        return 0
    ti = data.get("tool_input") or {}
    cmd = (ti.get("command") or "").strip()
    if not cmd or ti.get("run_in_background"):
        return 0
    if "tokcodec" in cmd or "# raw" in cmd or "|" in cmd or ">" in cmd:
        return 0
    if not NOISY.match(cmd):
        return 0
    level = os.environ.get("TOKCODEC_HOOK_LEVEL", "3")
    wrapped = f"set -o pipefail; {{ {cmd}; }} 2>&1 | tokcodec - -k log -l {level}"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {"command": wrapped},
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
