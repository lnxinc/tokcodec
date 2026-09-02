# Contributing

## Setup

```bash
uv sync
uv run pytest
uv run python bench/run.py
```

## Adding a transform

1. Put it in `tokpack/transforms/<kind>.py` as a pure `str -> str` function.
2. Wire it into a level in `tokpack/pipeline.py`. Lossless-in-meaning goes in level 1, anything that drops information goes in 2 or 3.
3. Add a test in `tests/` that asserts what the transform *keeps*, not just that output is shorter. A log transform must keep the failure line; a code transform must keep signatures and produce parseable output.
4. Run the benchmark and paste the new table into your PR description.

## Adding a language

Add the extension in `tokpack/detect.py`, implement `strip_comments`/`skeleton` in `tokpack/transforms/code.py`, add a sample under `samples/` and a description in `bench/run.py`.

## Style

Standard library only in `tokpack/` (tiktoken and anthropic are the only runtime deps, both optional at import time). Hooks must be stdlib-only Python 3 so they run without the venv.
