---
name: tokcodec
description: Cut tokens when reading large files, logs, JSON, or test/build/install output. Use before reading a file over ~300 lines, after running pytest/npm/cargo/go/make, or when a tool result is mostly repeated lines. Runs `tokcodec` to encode content at a chosen loss level.
allowed-tools: Bash(tokcodec *)
---

# tokcodec: read less, know the same

`tokcodec` encodes text for a language-model reader. Level 1 is lossless in
meaning (whitespace, ANSI, JSON layout, exact duplicate lines). Levels 2-3
are lossy: they drop what you rarely need on a first pass.

## When to use which level

| Situation | Command |
|---|---|
| First look at a big source file (Python, JS/TS, Go, Rust, Java, Kotlin, C#, C/C++, Swift, Ruby, …) | `tokcodec path/to/file -l 3` (signatures + structure, 70–90% fewer tokens) |
| Understand one file's logic, no editing yet | `tokcodec path/to/file.py -l 2` (comments and docstrings removed) |
| About to edit a file | Use the normal Read tool, or `tokcodec file -l 1`. Levels 2-3 change whitespace, so `old_string` edits against them will not match. |
| Test / build / install output | `pytest 2>&1 \| tokcodec - -k log -l 3` (duplicates collapsed, failures and summary kept) |
| Big JSON from an API or a fixture | `tokcodec response.json -l 3` (arrays sampled, still valid JSON) |
| Anything, to see the savings | add `-s` to print `before→after` token counts to stderr |

## Rules of thumb

- Start at level 3 for orientation, then Read only the ranges you need with `offset`/`limit`.
- Level 3 output marks what was dropped: `...  # 42 lines`, `/* … 12 lines */`, `… [300 lines omitted]`, `[×80]`. Those are your cue to go deeper if something matters.
- Never paste level 2-3 output back as an edit target.
