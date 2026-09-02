import json
import os
import subprocess
import sys

import pytest

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="needs sh/bash and a POSIX PATH")


def run_hook(which, payload, env=None, path=None):
    e = {**os.environ, **(env or {})}
    if path is not None:
        e["PATH"] = path
    r = subprocess.run([sys.executable, "-m", "tokcodec.cli", "hook", which], input=json.dumps(payload),
                       capture_output=True, text=True, check=True, env=e)
    return json.loads(r.stdout) if r.stdout.strip() else None


def with_tokcodec_on_path(tmp_path):
    """A PATH that has a `tokcodec` executable (a stub is enough for the presence check)."""
    stub = tmp_path / "tokcodec"
    stub.write_text("#!/bin/sh\nexit 0\n")
    stub.chmod(0o755)
    return f"{tmp_path}:{os.environ['PATH']}"


@posix_only
def test_bash_hook_wraps_noisy_commands(tmp_path):
    out = run_hook("bash", {"tool_name": "Bash", "tool_input": {"command": "npm test"}},
                   path=with_tokcodec_on_path(tmp_path))
    cmd = out["hookSpecificOutput"]["updatedInput"]["command"]
    assert "{ npm test; }" in cmd and 'tokcodec "$__t" -k log -l 3' in cmd
    assert '|| cat "$__t"' in cmd and "(exit $__rc)" in cmd


@posix_only
def test_bash_hook_fails_open_when_tokcodec_missing():
    out = run_hook("bash", {"tool_name": "Bash", "tool_input": {"command": "npm test"}}, path="/usr/bin:/bin")
    assert out is None


@posix_only
def test_bash_hook_leaves_quiet_piped_and_multiline_commands_alone(tmp_path):
    p = with_tokcodec_on_path(tmp_path)
    for c in ["ls -la", "git status", "pytest | tail -5", "npm test > out.txt", "tokcodec x.py", "pytest\necho done"]:
        assert run_hook("bash", {"tool_name": "Bash", "tool_input": {"command": c}}, path=p) is None


@posix_only
def test_bash_hook_respects_disable_and_background(tmp_path):
    p = with_tokcodec_on_path(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "pytest"}}
    assert run_hook("bash", payload, env={"TOKCODEC_HOOK_DISABLE": "1"}, path=p) is None
    payload["tool_input"]["run_in_background"] = True
    assert run_hook("bash", payload, path=p) is None


def test_bash_hook_garbage_input_is_ignored():
    r = subprocess.run([sys.executable, "-m", "tokcodec.cli", "hook", "bash"], input="not json",
                       capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == ""


@posix_only
def test_wrapped_command_preserves_output_and_exit_code(tmp_path):
    """Run the actual rewritten command in bash: with tokcodec on PATH and without."""
    from tokcodec.hooks import WRAP
    cmd = WRAP.format(cmd="echo '1 failed, 3 passed'; (exit 7)", level="3")  # a failing command, like pytest returning 1
    venv_bin = os.path.dirname(sys.executable)
    for path in (f"{venv_bin}:/usr/bin:/bin", "/usr/bin:/bin"):
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, env={**os.environ, "PATH": path})
        assert "1 failed, 3 passed" in r.stdout, path
        assert r.returncode == 7, path


def test_read_hook_denies_only_big_unranged_reads(tmp_path):
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * 20000)
    small = tmp_path / "small.py"
    small.write_text("x = 1\n")
    deny = run_hook("read", {"tool_name": "Read", "tool_input": {"file_path": str(big)}})
    assert deny["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "tokcodec" in deny["hookSpecificOutput"]["permissionDecisionReason"]
    assert run_hook("read", {"tool_name": "Read", "tool_input": {"file_path": str(small)}}) is None
    assert run_hook("read", {"tool_name": "Read", "tool_input": {"file_path": str(big), "offset": 10, "limit": 50}}) is None
