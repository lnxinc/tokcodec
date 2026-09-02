# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-09-02

### Added
- Encoder with four levels: 0 raw, 1 lossless, 2 light lossy, 3 heavy lossy (outline).
- Outlines for Python (via `ast`), JavaScript/TypeScript, Go, Rust, Java, Kotlin, C#, C/C++/Objective-C, Swift, Dart, Scala, PHP, Zig (brace scanner) and Ruby (`def … end`).
- Comment stripping for shell, Dockerfile, Makefile, YAML/TOML/INI, Perl/R/Elixir, SQL, Lua/Haskell, CSS/SCSS/Less and HTML/XML/SVG/Vue/Svelte.
- Codecs for JSON (minify, sample), logs (dedupe, timestamp removal, error-preserving truncation), diffs and prose.
- CLI: `encode` (default), `bench`, `count`, `why`, `langs`, `install`, `hook`, `serve`.
- Token counting via tiktoken `o200k_base` proxy, or Anthropic `count_tokens` with `--exact`.
- Claude Code integration: skill, fail-open `PreToolUse` hooks for Bash and Read, `tokcodec install` that merges `settings.json` and uninstalls cleanly; a plugin manifest (`.claude-plugin/`) and marketplace entry.
- `tokcodec serve`: MCP server over stdio with `read_compact`, `compact_text`, `token_count` (extra: `tokcodec[mcp]`).
- `npx tokcodec` launcher that uses `tokcodec`, `uvx` or `pipx` if present and otherwise downloads `uv` once, so it runs with no Python installed.
- Reproducible benchmark (`bench/run.py`) on 13 real-world samples, and a fidelity harness (`bench/fidelity/`) that measures what each level loses.

### Security
- Hooks fail open: if `tokcodec` is missing or fails, the original command output and exit code are shown unchanged. `TOKCODEC_HOOK_DISABLE=1` turns them off.

[Unreleased]: https://github.com/lnxinc/tokcodec/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/lnxinc/tokcodec/releases/tag/v0.1.0
