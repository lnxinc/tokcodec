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
    assert not (home / ".claude" / "hooks" / "tokcodec").exists()  # no scripts on disk any more
    s = json.loads((home / ".claude" / "settings.json").read_text())
    assert s["theme"] == "dark"
    bash = next(g for g in s["hooks"]["PreToolUse"] if g["matcher"] == "Bash")
    assert [h["command"] for h in bash["hooks"]][0] == "echo mine"  # user's hook kept, first
    assert any(h["command"] == "tokcodec hook bash" for h in bash["hooks"])
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


def test_plugin_skill_matches_installed_skill():
    """The plugin ships a copy of the skill; keep it identical to the package asset."""
    root = Path(__file__).parent.parent
    a = (root / "tokcodec" / "assets" / "claude_code" / "SKILL.md").read_text(encoding="utf-8")
    b = (root / "skills" / "tokcodec" / "SKILL.md").read_text(encoding="utf-8")
    assert a == b


def test_plugin_manifests_are_valid_json_and_consistent():
    root = Path(__file__).parent.parent
    plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    hooks = json.loads((root / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "tokcodec" and market["plugins"][0]["name"] == "tokcodec"
    assert plugin["version"] == market["plugins"][0]["version"]
    cmds = [h["command"] for g in hooks["hooks"]["PreToolUse"] for h in g["hooks"]]
    assert cmds == ["tokcodec hook bash", "tokcodec hook read"]
