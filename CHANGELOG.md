# Changelog

## 0.1.0 (2026-09-02)

Initial release.

- Levels 0-3 for Python, JS/TS, Go, Rust, Java, Kotlin, C#, C/C++, Swift, Dart, Scala, PHP, Zig, Ruby (outlines), plus comment stripping for shell, YAML/TOML, Perl/R/Elixir, SQL, Lua/Haskell, CSS and HTML/XML; JSON, log, diff and text codecs
- PHP: `#` comments, attributes preserved, `<?php` content detection
- `tokcodec langs` lists kinds
- CLI: `encode` (default), `bench`, `count`, `why`
- Proxy token counting via tiktoken, exact counting via Anthropic `count_tokens`
- Claude Code skill, Bash hook, Read hook, `tokcodec install`
- `npx tokcodec` launcher (npm package wraps the Python CLI)
