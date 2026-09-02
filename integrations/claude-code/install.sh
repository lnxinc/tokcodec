#!/usr/bin/env bash
# Installs the tokpack skill and hooks for Claude Code (user level).
#   ./integrations/claude-code/install.sh            skill + hooks
#   ./integrations/claude-code/install.sh --skill    skill only (no automatic rewriting)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/tokpack"
HOOK_DIR="$HOME/.claude/hooks/tokpack"

command -v tokpack >/dev/null || {
  echo "tokpack is not on PATH. Install it first:  uv tool install tokpack   (or: pipx install tokpack)"; exit 1; }

mkdir -p "$SKILL_DIR" "$HOOK_DIR"
cp "$HERE/skill/SKILL.md" "$SKILL_DIR/SKILL.md"
echo "skill  -> $SKILL_DIR/SKILL.md"

if [[ "${1:-}" != "--skill" ]]; then
  cp "$HERE/hooks/"*.py "$HOOK_DIR/"
  echo "hooks  -> $HOOK_DIR/"
  echo
  echo "Now add the hooks to ~/.claude/settings.json (merge with what you have):"
  echo
  cat "$HERE/settings.example.json"
  echo
  echo "Env knobs: TOKPACK_HOOK_LEVEL=2|3  TOKPACK_READ_MAX_KB=64  TOKPACK_HOOK_DISABLE=1"
fi
