"""`tokcodec install` - set up the Claude Code skill and hooks.

    tokcodec install                 user level: ~/.claude  (skill + hooks)
    tokcodec install --project       this repo: ./.claude
    tokcodec install --skill-only    no automatic command rewriting
    tokcodec install --uninstall     remove what we added
    tokcodec install --dry-run       show the plan

Hooks are registered in settings.json by merging, never overwriting, and are
identified by a `# tokcodec` marker so uninstall removes only ours.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).parent / "assets" / "claude_code"
MARK = "tokcodec"


def _hook_entry(script: Path) -> dict:
    return {"type": "command", "command": f"python3 {script}"}


def _is_ours(entry: dict) -> bool:
    return MARK in str(entry.get("command", ""))


def _merge_hooks(settings: dict, hook_dir: Path, remove: bool = False) -> dict:
    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    wanted = {"Bash": _hook_entry(hook_dir / "bash_hook.py"), "Read": _hook_entry(hook_dir / "read_hook.py")}
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
    hook_dir = root / "hooks" / MARK
    settings_path = root / ("settings.local.json" if project else "settings.json")
    plan: list[str] = []

    if uninstall:
        plan.append(f"remove {skill_dir}")
        plan.append(f"remove {hook_dir}")
        plan.append(f"strip tokcodec hooks from {settings_path}")
    else:
        plan.append(f"write  {skill_dir / 'SKILL.md'}")
        if not skill_only:
            plan.append(f"write  {hook_dir / 'bash_hook.py'}, read_hook.py")
            plan.append(f"merge  PreToolUse hooks into {settings_path}")

    print("\n".join(("[dry-run] " if dry_run else "") + p for p in plan), file=out)
    if dry_run:
        return 0

    if uninstall:
        shutil.rmtree(skill_dir, ignore_errors=True)
        shutil.rmtree(hook_dir, ignore_errors=True)
        if settings_path.exists():
            settings = json.loads(settings_path.read_text() or "{}")
            settings_path.write_text(json.dumps(_merge_hooks(settings, hook_dir, remove=True), indent=2) + "\n")
        print("done. tokcodec itself is still installed; remove with `uv tool uninstall tokcodec` or `pipx uninstall tokcodec`.", file=out)
        return 0

    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(ASSETS / "SKILL.md", skill_dir / "SKILL.md")
    if not skill_only:
        hook_dir.mkdir(parents=True, exist_ok=True)
        for name in ("bash_hook.py", "read_hook.py"):
            shutil.copy(ASSETS / name, hook_dir / name)
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings = json.loads(settings_path.read_text() or "{}") if settings_path.exists() else {}
        settings_path.write_text(json.dumps(_merge_hooks(settings, hook_dir), indent=2) + "\n")
    if shutil.which(MARK) is None:
        print("note: `tokcodec` is not on PATH. The hooks call it by name, so install it permanently:\n"
              "      uv tool install tokcodec   (or: pipx install tokcodec)", file=out)
    print("done. Restart Claude Code (or open a new session) to pick up the skill and hooks.\n"
          "knobs: TOKCODEC_HOOK_LEVEL=2|3  TOKCODEC_READ_MAX_KB=64  TOKCODEC_HOOK_DISABLE=1", file=out)
    return 0
