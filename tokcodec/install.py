"""`tokcodec install` - set up the Claude Code skill and hooks.

    tokcodec install                 user level: ~/.claude  (skill + hooks)
    tokcodec install --project       this repo: ./.claude
    tokcodec install --skill-only    no automatic command rewriting
    tokcodec install --uninstall     remove what we added
    tokcodec install --dry-run       show the plan

Hooks are registered in settings.json as `tokcodec hook bash` / `tokcodec hook read`
(no python3, no paths, works on Windows) by merging, never overwriting. Uninstall
removes only entries containing `tokcodec`.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).parent / "assets" / "claude_code"
MARK = "tokcodec"


def _hook_entry(which: str) -> dict:
    return {"type": "command", "command": f"tokcodec hook {which}"}


def _is_ours(entry: dict) -> bool:
    return MARK in str(entry.get("command", ""))


def _merge_hooks(settings: dict, remove: bool = False) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    wanted = {"Bash": _hook_entry("bash"), "Read": _hook_entry("read")}
    # drop ours first (idempotent re-install / uninstall)
    for group in pre:
        group["hooks"] = [h for h in group.get("hooks", []) if not _is_ours(h)]
    pre[:] = [g for g in pre if g.get("hooks")]
    if not remove:
        for matcher, entry in wanted.items():
            for group in pre:
                if group.get("matcher") == matcher:
                    group["hooks"].append(entry)
                    break
            else:
                pre.append({"matcher": matcher, "hooks": [entry]})
    if not pre:
        hooks.pop("PreToolUse", None)
    if not hooks:
        settings.pop("hooks", None)
    return settings


def run(project: bool = False, skill_only: bool = False, uninstall: bool = False,
        dry_run: bool = False, home: Path | None = None, out=sys.stdout) -> int:
    root = (Path.cwd() if project else (home or Path.home())) / ".claude"
    skill_dir = root / "skills" / MARK
    hook_dir = root / "hooks" / MARK  # legacy location from 0.1.0 dev builds; removed on (un)install
    settings_path = root / ("settings.local.json" if project else "settings.json")
    plan: list[str] = []

    if uninstall:
        plan.append(f"remove {skill_dir}")
        plan.append(f"strip tokcodec hooks from {settings_path}")
    else:
        plan.append(f"write  {skill_dir / 'SKILL.md'}")
        if not skill_only:
            plan.append(f"merge  `tokcodec hook bash` / `tokcodec hook read` into {settings_path}")

    print("\n".join(("[dry-run] " if dry_run else "") + p for p in plan), file=out)
    if dry_run:
        return 0

    if uninstall:
        shutil.rmtree(skill_dir, ignore_errors=True)
        shutil.rmtree(hook_dir, ignore_errors=True)
        if settings_path.exists():
            settings = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
            settings_path.write_text(json.dumps(_merge_hooks(settings, remove=True), indent=2) + "\n", encoding="utf-8")
        print("done. tokcodec itself is still installed; remove with `uv tool uninstall tokcodec` or `pipx uninstall tokcodec`.", file=out)
        return 0

    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ASSETS / "SKILL.md", skill_dir / "SKILL.md")
    shutil.rmtree(hook_dir, ignore_errors=True)
    if not skill_only:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = json.loads(settings_path.read_text(encoding="utf-8") or "{}") if settings_path.exists() else {}
        settings_path.write_text(json.dumps(_merge_hooks(settings), indent=2) + "\n", encoding="utf-8")
    if shutil.which(MARK) is None:
        print("note: `tokcodec` is not on PATH. The hooks run `tokcodec hook ...` by name and do nothing\n"
              "      until it is, so install it permanently: uv tool install tokcodec  (or: pipx install tokcodec)", file=out)
    print("done. Restart Claude Code (or open a new session) to pick up the skill and hooks.\n"
          "knobs: TOKCODEC_HOOK_LEVEL=2|3  TOKCODEC_READ_MAX_KB=64  TOKCODEC_HOOK_DISABLE=1", file=out)
    return 0
