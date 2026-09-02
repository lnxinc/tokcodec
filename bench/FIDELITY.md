# Fidelity results

**Not yet run.** The harness and 104 questions (8 per sample, 13 samples) are in place; running it needs an Anthropic API key.

```bash
uv run --extra bench python bench/fidelity/run.py --estimate   # cost first, no API calls
uv run --extra bench python bench/fidelity/run.py              # writes this file
```

What it measures: for every sample in `samples/`, 8 questions with checkable answers (signatures, values, failure lines, and details that levels 2 and 3 are *expected* to lose). Each question is asked at levels 0–3, graded, and every wrong answer is listed here unedited. Questions live in `bench/fidelity/questions/`; the expected-survival level of each question is declared up front so the harness can't be tuned after the fact.

Expected-survival distribution (from `--dry-run`):

| survives up to | questions |
|---|---:|
| L3 (signatures, names, imports, failure lines, totals) | 68 |
| L2 (function-body logic, JSON items past the 8th) | 24 |
| L1 (comment and docstring contents) | 12 |
