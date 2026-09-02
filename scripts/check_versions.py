#!/usr/bin/env python3
"""Fail if pyproject.toml, npm/package.json, tokcodec/__init__.py and the
plugin manifest disagree on the version, or (given a tag) if the tag differs."""
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
py = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
npm = json.loads((ROOT / "npm" / "package.json").read_text())["version"]
init = re.search(r'__version__ = "([^"]+)"', (ROOT / "tokcodec" / "__init__.py").read_text()).group(1)
plugin_path = ROOT / ".claude-plugin" / "plugin.json"
plugin = json.loads(plugin_path.read_text())["version"] if plugin_path.exists() else py
tag = sys.argv[1].lstrip("v") if len(sys.argv) > 1 else py

versions = {"pyproject.toml": py, "npm/package.json": npm, "tokcodec/__init__.py": init,
            ".claude-plugin/plugin.json": plugin, "tag": tag}
if len(set(versions.values())) != 1:
    for k, v in versions.items():
        print(f"  {k:<28} {v}")
    print("version mismatch", file=sys.stderr)
    sys.exit(1)
print(f"version {py} consistent across {len(versions) - 1} files")
