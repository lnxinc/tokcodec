# Contributing

## Setup

```bash
uv sync
uv run pytest
uv run python bench/run.py
```

## Adding a transform

1. Put it in `tokcodec/transforms/<kind>.py` as a pure `str -> str` function.
2. Wire it into a level in `tokcodec/pipeline.py`. Lossless-in-meaning goes in level 1, anything that drops information goes in 2 or 3.
3. Add a test in `tests/` that asserts what the transform *keeps*, not just that output is shorter. A log transform must keep the failure line; a code transform must keep signatures and produce parseable output.
4. Run the benchmark and paste the new table into your PR description.

## Adding a language

Add the extension in `tokcodec/detect.py`, implement `strip_comments`/`skeleton` in `tokcodec/transforms/code.py`, add a sample under `samples/` and a description in `bench/run.py`.

## Layout

- `tokcodec/` the Python package (engine, CLI, `install` command, Claude Code assets under `tokcodec/assets/`)
- `npm/` the `npx tokcodec` launcher; it only locates or bootstraps the Python CLI, no logic lives there
- `bench/` reproducible benchmark; `samples/` inputs with attribution

## Style

Standard library only in `tokcodec/` (tiktoken and anthropic are the only runtime deps, both optional at import time). Hooks must be stdlib-only Python 3 so they run without the venv.
