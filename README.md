<p align="center">
  <img src="assets/hero.svg" alt="tokcodec turns a 15,089-token pytest log into 231 tokens with the failure intact" width="820">
</p>

<h1 align="center">tokcodec</h1>

<p align="center">
  <b>A codec for LLM context.</b><br>
  Video codecs throw away what the eye can't see. tokcodec throws away what the model doesn't need.<br>
  Your AI coding tools read less, know the same, and cost 30–95% fewer tokens.
</p>

<p align="center">
  <a href="https://github.com/YOUR_GITHUB/tokcodec/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/YOUR_GITHUB/tokcodec/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/tokcodec/"><img alt="PyPI" src="https://img.shields.io/pypi/v/tokcodec?color=blue"></a>
  <a href="https://www.npmjs.com/package/tokcodec"><img alt="npm" src="https://img.shields.io/npm/v/tokcodec?color=cb3837"></a>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-blue">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

## Try it in 10 seconds

```bash
npx tokcodec why path/to/any/file.py     # see the token math for yourself
npx tokcodec install                      # wire it into Claude Code (skill + hooks)
```

That's it. From now on Claude Code's `pytest`, `npm install`, `cargo build` and friends come back squeezed, and it gets an outline before reading a 2,000-line file.

Prefer Python tooling? `uvx tokcodec ...` or `pipx run tokcodec ...` do the same. Permanent install: `uv tool install tokcodec` / `pipx install tokcodec`.

## What you get

- **Smaller tool results, same signal.** Repeated log lines collapse to `[×80]`. The failure, its traceback and the summary line stay.
- **Outlines instead of walls of code.** Level 3 keeps imports, classes, signatures and the first docstring line, and marks each dropped body with `...  # 42 lines`. Valid Python, valid JSON, readable JS.
- **A number, not a vibe.** Every run can print `before → after` token counts. `tokcodec bench` runs the whole table on your own repo.
- **Nothing hidden.** Every level tells the reader what it removed, so an agent knows when to look deeper.

## Benchmark

Real files, reproducible with `uv run python bench/run.py`. Details in [`bench/RESULTS.md`](bench/RESULTS.md).

<!-- BENCH -->
| file | kind | what it is | raw tokens | L1 lossless | L2 light | L3 heavy |
|---|---|---|---:|---:|---:|---:|
| `api_response.json` | json | pretty-printed REST response, 120 records | 11,138 | 6,983 (−37%) | 6,983 (−37%) | 493 (−96%) |
| `argparse.py` | python | CPython stdlib `argparse.py` | 21,198 | 21,195 (−0%) | 15,688 (−26%) | 3,501 (−83%) |
| `decoder.py` | python | CPython stdlib `json/decoder.py` | 3,159 | 3,159 (−0%) | 2,105 (−33%) | 599 (−81%) |
| `npm_module.js` | js | `glob/dist/esm/walker.js` from npm | 2,851 | 2,851 (−0%) | 2,520 (−12%) | 520 (−82%) |
| `pytest_run.log` | log | pytest run, 412 tests, ANSI colour, timestamps, 1 failure | 15,089 | 15,073 (−0%) | 231 (−98%) | 231 (−98%) |
| **total** | | | **53,435** | **49,261 (−8%)** | **27,527 (−48%)** | **5,344 (−90%)** |
<!-- /BENCH -->

## Why not just gzip it?

Because bytes and tokens are different currencies. A BPE tokenizer turns high-entropy text into roughly one token per one or two characters, and the model can't inflate gzip in its head anyway. Every byte-level trick makes the token count *worse*:

<!-- WHY -->
| variant | bytes | tokens | vs original | model can read it? |
|---|---:|---:|---:|---|
| original | 12,873 | 3,159 | +0% | yes |
| gzip + base64 | 4,876 | 3,297 | +4% | no, the model cannot inflate gzip |
| vowels removed | 11,075 | 3,908 | +24% | partly, and it guesses wrong |
| tokcodec L1 | 12,866 | 3,159 | +0% | yes, lossless |
| tokcodec L2 | 7,996 | 2,105 | -33% | yes, comments gone |
| tokcodec L3 | 1,957 | 599 | -81% | yes, bodies gone (outline) |
<!-- /WHY -->

Token compression has to remove *information the reader doesn't need*, not bytes. That is what tokcodec does, in graded levels.

## Levels

| Level | Name | What happens | Edit against it? |
|---|---|---|---|
| 0 | raw | nothing | yes |
| 1 | **lossless** | ANSI codes, `\r`, trailing whitespace, blank-line runs, JSON re-serialised compact, exact duplicate log lines → `[×N]` | yes |
| 2 | **light** | + timestamps and long hex ids out of logs, near-duplicates collapsed, comments and docstrings out of code | no (whitespace differs) |
| 3 | **heavy** | + function bodies → `...  # N lines` (Python) or `{ /* … N lines */ }` (JS/TS), indentation shrunk, logs cut to head + tail + every error/warning line with context, JSON arrays capped at 8 items and strings at 200 chars | no |

Levels 2 and 3 are for *reading*. When an agent needs to change a file it should read it losslessly, and the bundled skill says so.

## Usage

```bash
tokcodec FILE                    # level 2, kind auto-detected
tokcodec FILE -l 3 -s            # heavy level, token stats on stderr
cat big.json | tokcodec - -k json -l 1
tokcodec bench src/              # savings table for a whole directory
tokcodec count FILE              # token count
tokcodec why FILE                # the gzip table above, for any file
tokcodec install [--project] [--skill-only] [--uninstall] [--dry-run]
```

Kinds are auto-detected from extension and content: `python`, `js` (also ts/tsx/jsx), `json`, `log`, `diff`, `text`. Override with `-k`.

Add `--exact` to count with Anthropic's `count_tokens` endpoint instead of the local proxy tokenizer. It is free and needs `ANTHROPIC_API_KEY` or an `ant auth login` profile.

### As a library

```python
from tokcodec import encode

r = encode(open("app.log").read(), level=3, kind="log")
print(r.encoded)
print(r.tokens_before, r.tokens_after, r.steps)
# 15089 231 ['lossless-text', 'log-fuzzy', 'log-truncate']
```

## Claude Code integration

`tokcodec install` sets up three things under `~/.claude/` (or `./.claude/` with `--project`):

1. **A skill** that teaches Claude when to reach for tokcodec instead of reading a huge file whole, and which level to use.
2. **A Bash hook** (`PreToolUse`) that rewrites noisy commands (`pytest`, `npm install`, `cargo build`, `git pull`, …) to pipe through `tokcodec - -k log -l 3`. Claude never sees the 900 lines of dots.
3. **A Read hook** (`PreToolUse`) that stops whole-file reads above 64 KB and points Claude at `tokcodec file -l 3` for an outline, then ranged reads.

Settings are merged, never overwritten, and `--uninstall` removes exactly what was added. Knobs: `TOKCODEC_HOOK_LEVEL=2|3`, `TOKCODEC_READ_MAX_KB=64`, `TOKCODEC_HOOK_DISABLE=1`.

Using Cursor, Codex, Aider or Gemini CLI? tokcodec is a plain stdin/stdout filter. Drop the text of [`SKILL.md`](tokcodec/assets/claude_code/SKILL.md) into your agent's instructions file and pipe away.

## How it works

```
input ─▶ detect kind ─▶ L1 lossless ─▶ L2 light lossy ─▶ L3 heavy lossy ─▶ count tokens
```

- **Python** goes through `ast` and `tokenize`, so a `#` inside a string is never mistaken for a comment and skeletons always parse.
- **JS/TS** uses a small scanner that tracks strings, template literals and comments while matching braces.
- **Logs** dedupe on a fuzzy key (digits and durations normalised), then keep head, tail and every line matching error/fail/warn/exception/traceback/summary patterns, with one line of context.
- **JSON** is parsed and re-emitted, so output is always valid JSON.

## Honest limits

- The default counter is tiktoken's `o200k_base`, because Anthropic doesn't publish Claude's tokenizer. Ratios transfer well; absolute numbers can differ by 10–30%. `--exact` gives real counts.
- tokcodec does not replace prompt caching. Caching makes re-sent context cheap; tokcodec makes it smaller to begin with. Use both.
- Languages other than Python and JS/TS get the text and log treatment only, for now.

## Roadmap

- [ ] More languages via tree-sitter (Go, Rust, Java, C#)
- [ ] Diff-aware mode: skeleton everything except the hunks that changed
- [ ] Session-level dedupe: never send the same file twice in one conversation
- [ ] `tokcodec serve`: an MCP server exposing `read_compact`
- [ ] Learned importance scoring for log lines

## Contributing

```bash
git clone https://github.com/YOUR_GITHUB/tokcodec && cd tokcodec
uv sync && uv run pytest && uv run python bench/run.py
```

Every transform ships with a test that proves what it *keeps*: a failure line, a signature, valid JSON. See [CONTRIBUTING.md](CONTRIBUTING.md). Ideas and benchmark results from your own repos are very welcome in issues.

## License

MIT
