import json
from pathlib import Path

from tokcodec import install


def test_install_then_uninstall_is_clean(tmp_path):
    home = tmp_path
    existing = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo mine"}]}]},
                "theme": "dark"}
    (home / ".claude").mkdir()
    (home / ".claude" / "settings.json").write_text(json.dumps(existing))

    assert install.run(home=home) == 0
    assert (home / ".claude" / "skills" / "tokcodec" / "SKILL.md").exists()
    assert (home / ".claude" / "hooks" / "tokcodec" / "bash_hook.py").exists()
    s = json.loads((home / ".claude" / "settings.json").read_text())
    assert s["theme"] == "dark"
    bash = next(g for g in s["hooks"]["PreToolUse"] if g["matcher"] == "Bash")
    assert [h["command"] for h in bash["hooks"]][0] == "echo mine"  # user's hook kept, first
    assert any("tokcodec/bash_hook.py" in h["command"] for h in bash["hooks"])
    assert any(g["matcher"] == "Read" for g in s["hooks"]["PreToolUse"])

    # idempotent
    install.run(home=home)
    s = json.loads((home / ".claude" / "settings.json").read_text())
    bash = next(g for g in s["hooks"]["PreToolUse"] if g["matcher"] == "Bash")
    assert sum("tokcodec" in h["command"] for h in bash["hooks"]) == 1

    assert install.run(home=home, uninstall=True) == 0
    s = json.loads((home / ".claude" / "settings.json").read_text())
    assert s == existing
    assert not (home / ".claude" / "skills" / "tokcodec").exists()


def test_skill_only_and_dry_run(tmp_path, capsys):
    install.run(home=tmp_path, skill_only=True)
    assert (tmp_path / ".claude" / "skills" / "tokcodec" / "SKILL.md").exists()
    assert not (tmp_path / ".claude" / "settings.json").exists()
    install.run(home=tmp_path / "other", dry_run=True)
    assert not (tmp_path / "other").exists()
