import json
import subprocess
import sys
from pathlib import Path

HOOKS = Path(__file__).parent.parent / "integrations" / "claude-code" / "hooks"


def run_hook(name, payload, env=None):
    import os
    r = subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(payload),
                       capture_output=True, text=True, check=True, env={**os.environ, **(env or {})})
    return json.loads(r.stdout) if r.stdout.strip() else None


def test_bash_hook_wraps_noisy_commands():
    out = run_hook("bash_hook.py", {"tool_name": "Bash", "tool_input": {"command": "npm test"}})
    cmd = out["hookSpecificOutput"]["updatedInput"]["command"]
    assert cmd.startswith("set -o pipefail; { npm test; }") and "tokpack - -k log" in cmd


def test_bash_hook_leaves_quiet_and_piped_commands_alone():
    for c in ["ls -la", "git status", "pytest | tail -5", "npm test > out.txt", "tokpack x.py"]:
        assert run_hook("bash_hook.py", {"tool_name": "Bash", "tool_input": {"command": c}}) is None


def test_bash_hook_respects_disable_and_background():
    p = {"tool_name": "Bash", "tool_input": {"command": "pytest"}}
    assert run_hook("bash_hook.py", p, env={"TOKPACK_HOOK_DISABLE": "1"}) is None
    p["tool_input"]["run_in_background"] = True
    assert run_hook("bash_hook.py", p) is None


def test_read_hook_denies_only_big_unranged_reads(tmp_path):
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * 20000)
    small = tmp_path / "small.py"
    small.write_text("x = 1\n")
    deny = run_hook("read_hook.py", {"tool_name": "Read", "tool_input": {"file_path": str(big)}})
    assert deny["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "tokpack" in deny["hookSpecificOutput"]["permissionDecisionReason"]
    assert run_hook("read_hook.py", {"tool_name": "Read", "tool_input": {"file_path": str(small)}}) is None
    assert run_hook("read_hook.py", {"tool_name": "Read", "tool_input": {"file_path": str(big), "offset": 10, "limit": 50}}) is None
