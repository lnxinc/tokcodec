<h1 align="center">tokpack</h1>
<p align="center"><b>A codec for LLM context.</b><br>
Cut the tokens Claude Code and other AI tools burn on logs, JSON and source files by 30–95%.<br>
Lossless or lossy, you pick the level.</p>

<p align="center">
  <a href="https://github.com/YOUR_GITHUB/tokpack/actions"><img alt="CI" src="https://github.com/YOUR_GITHUB/tokpack/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python 3.12+" src="https://img.shields.io/badge/python-3.12%2B-blue">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green">
</p>

```console
$ pytest 2>&1 | tokpack - -k log -l 3 -s
============================= test session starts ==============================
collected 412 items

INFO  tests/test_api_1.py::test_case_1 PASSED  (73ms)  [×79]
DEBUG  retrying connection to db (attempt 1)  [×40]
ERROR tests/test_billing.py::test_refund FAILED
    def test_refund():
        r = refund(order_id='8f3a9c2b4d1e…')
>       assert r.status == 'ok'
E       AssertionError: assert 'declined' == 'ok'
INFO  tests/test_api_8.py::test_case_80 PASSED  (80ms)  [×320]
========================= 1 failed, 411 passed in 42.11s =========================
[tokpack kind=log level=3 15089→231 tok (-98%)]
```

Same failure, same summary, 98% fewer tokens.

## Why this exists

Every tool result an AI coding agent reads goes into its context window and onto your bill. Most of it is filler: 400 lines of `PASSED`, pretty-printed JSON that is half whitespace, 2,000-line source files when the agent only needed the shape of the module.

Video and image codecs solved the same problem for a different consumer. They throw away what the eye can't see. tokpack throws away what the model doesn't need, in graded levels, and shows you the token count before and after.

## Benchmark

Run `uv run python bench/run.py` to reproduce. Full details in [`bench/RESULTS.md`](bench/RESULTS.md).

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

Because bytes and tokens are different currencies. A BPE tokenizer turns high-entropy text into roughly one token per one or two characters, and the model cannot inflate gzip in its head anyway. Every "clever" byte-level trick makes the token count worse:

<!-- WHY -->
| variant | bytes | tokens | vs original | model can read it? |
|---|---:|---:|---:|---|
| original | 12,873 | 3,159 | +0% | yes |
| gzip + base64 | 4,876 | 3,296 | +4% | no, the model cannot inflate gzip |
| vowels removed | 11,075 | 3,908 | +24% | partly, and it guesses wrong |
| tokpack L1 | 12,866 | 3,159 | +0% | yes, lossless |
| tokpack L2 | 7,996 | 2,105 | -33% | yes, comments gone |
| tokpack L3 | 1,957 | 599 | -81% | yes, bodies gone (outline) |
<!-- /WHY -->

Token compression has to remove *information the reader doesn't need*, not bytes.

## Install

```bash
uv tool install tokpack        # or: pipx install tokpack
tokpack --version
```

From source:

```bash
git clone https://github.com/YOUR_GITHUB/tokpack && cd tokpack
uv sync && uv run tokpack samples/pytest_run.log -l 3 -s
```

## Usage

```bash
tokpack FILE                    # level 2, kind auto-detected
tokpack FILE -l 3 -s            # heavy level, print token stats to stderr
cat big.json | tokpack - -k json -l 1
tokpack bench path/ or files    # table of savings per level
tokpack count FILE              # token count
tokpack why FILE                # the gzip table above, for any file
```

Add `--exact` to any command to count with Anthropic's `count_tokens` endpoint instead of the local proxy tokenizer (needs `ANTHROPIC_API_KEY` or an `ant auth login` profile; it is free).

### Levels

| Level | Name | What happens | Safe to edit against? |
|---|---|---|---|
| 0 | raw | nothing | yes |
| 1 | **lossless** | ANSI codes, `\r`, trailing whitespace, runs of blank lines, JSON re-serialised compact, exact duplicate log lines collapsed to `[×N]` | yes |
| 2 | **light** | + timestamps and long hex ids stripped from logs, near-duplicate lines collapsed, comments and docstrings removed from code | no (whitespace differs) |
| 3 | **heavy** | + function bodies replaced by `...  # N lines` (Python, valid syntax) or `{ /* … N lines */ }` (JS/TS), indentation shrunk, logs truncated to head + tail + every error/warning line with context, JSON arrays capped at 8 items and strings at 200 chars (still valid JSON) | no |

Level 3 output always marks what was dropped, so the reader knows where to look deeper.

### Content kinds

Auto-detected from extension and content: `python`, `js` (also ts/tsx/jsx), `json`, `log`, `diff`, `text`. Override with `-k`.

### Library

```python
from tokpack import encode

r = encode(open("app.log").read(), level=3, kind="log")
print(r.encoded)
print(r.tokens_before, r.tokens_after, r.steps)   # 15089 231 ['lossless-text', 'log-fuzzy', 'log-truncate']
```

## Claude Code integration

tokpack is a plain stdin/stdout CLI, so it works anywhere. For Claude Code there are three pieces, all in [`integrations/claude-code/`](integrations/claude-code):

1. **A skill** (`SKILL.md`) that teaches Claude when to reach for `tokpack` instead of reading a 2,000-line file whole, and which level to use.
2. **A Bash hook** (`PreToolUse`) that automatically rewrites noisy commands (`pytest`, `npm install`, `cargo build`, `git pull`, ...) to pipe through `tokpack - -k log -l 3`. Claude never sees the 900 lines of dots.
3. **A Read hook** (`PreToolUse`, opt-in) that stops whole-file reads above 64 KB and points Claude at `tokpack file -l 3` for an outline first, then ranged reads.

```bash
uv tool install tokpack
./integrations/claude-code/install.sh          # skill + hooks
./integrations/claude-code/install.sh --skill  # skill only
```

Then merge `integrations/claude-code/settings.example.json` into `~/.claude/settings.json`. Knobs: `TOKPACK_HOOK_LEVEL=2|3`, `TOKPACK_READ_MAX_KB=64`, `TOKPACK_HOOK_DISABLE=1`.

Works with any other agent that can run shell commands or read a CLAUDE.md-style instruction file: Cursor, Codex, Aider, Gemini CLI. Point them at the skill text.

## How it works

```
input ──▶ detect kind ──▶ level 1: lossless text + kind-specific lossless
                      ──▶ level 2: kind-specific light lossy
                      ──▶ level 3: kind-specific heavy lossy
                      ──▶ count tokens before/after
```

- **Python** uses `ast` and `tokenize`, so comment stripping never touches a `#` inside a string and skeletons stay valid Python.
- **JS/TS** uses a small scanner that tracks strings, template literals and comments while matching braces.
- **Logs** dedupe with a fuzzy key (digits and durations normalised), then keep head, tail and any line matching error/fail/warn/exception/traceback/summary patterns with one line of context.
- **JSON** is parsed and re-emitted, so the output is always valid JSON.

## What it does not do

- It is not the Claude tokenizer. Anthropic does not publish one, so the default counter is tiktoken's `o200k_base`. The *ratios* transfer well; absolute numbers can differ by 10–30%. Use `--exact` for real counts.
- It does not replace prompt caching. Caching makes re-sent context cheap. tokpack makes the context smaller in the first place. Use both.
- Levels 2 and 3 are for reading, not editing. If an agent needs to change a file, it should read it losslessly.

## Roadmap

- [ ] More languages via tree-sitter (Go, Rust, Java, C#)
- [ ] Diff-aware mode: skeleton everything except the hunks that changed
- [ ] Learned importance scoring for log lines (small local model)
- [ ] Session-level dedupe: never send the same file twice in one conversation
- [ ] `tokpack serve`: an MCP server exposing `read_compact`

## Contributing

`uv sync && uv run pytest`. Benchmarks: `uv run python bench/run.py`. Every transform needs a test that proves it keeps what it promises to keep (a failure line, a signature, valid JSON). See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
