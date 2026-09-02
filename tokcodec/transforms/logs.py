"""Log / tool-output codec.

Logs are the most wasteful thing a coding agent reads: progress bars, repeated
lines, timestamps, and 900 lines of "ok" before the one line that matters.
"""
from __future__ import annotations

import re

TIMESTAMP = re.compile(
    r"^\[?(\d{4}-\d{2}-\d{2}[T ])?\d{2}:\d{2}:\d{2}([.,]\d+)?(Z|[+-]\d{2}:?\d{2})?\]?\s*"
)
EPOCH_PREFIX = re.compile(r"^\[?\d{10}(\.\d+)?\]?\s+")
PROGRESS = re.compile(r"^\s*(\[[=\-#> ]+\]|[█░▓]+|\d{1,3}%|\.{3,}|Downloading|Receiving objects|Resolving deltas).*$")
HEX_ID = re.compile(r"\b[0-9a-f]{32,}\b")
DURATION = re.compile(r"\s*\(\d+(\.\d+)?\s?(ms|s|m)\)$")

INTERESTING = re.compile(
    r"\b(error|fail(ed|ure)?|exception|traceback|warn(ing)?|fatal|panic|assert|"
    r"denied|refused|timeout|not found|undefined|null pointer|segfault|exit code|"
    r"passed|skipped|summary|E\s{2,})\b",
    re.I,
)


def strip_timestamps(text: str) -> str:
    out = []
    for l in text.split("\n"):
        l2 = TIMESTAMP.sub("", l)
        l2 = EPOCH_PREFIX.sub("", l2)
        out.append(l2)
    return "\n".join(out)


def drop_progress(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if not PROGRESS.match(l))


def shorten_ids(text: str) -> str:
    return HEX_ID.sub(lambda m: m.group(0)[:12] + "…", text)


def dedupe(text: str, fuzzy: bool = True) -> str:
    """Collapse runs of identical (or, fuzzily, near-identical) lines into one + [×N]."""
    out: list[str] = []
    prev_key = None
    run = 0

    def key(l: str) -> str:
        if not fuzzy:
            return l
        k = re.sub(r"\d+", "#", l)
        k = DURATION.sub("", k)
        return k

    def flush():
        if run > 1:
            out[-1] = f"{out[-1]}  [×{run}]"

    for l in text.split("\n"):
        k = key(l)
        if k == prev_key and l.strip():
            run += 1
            continue
        flush()
        out.append(l)
        prev_key, run = k, 1
    flush()
    return "\n".join(out)


def smart_truncate(text: str, head: int = 40, tail: int = 60, max_lines: int = 200) -> str:
    """Keep head, tail, and every 'interesting' line in between (with 1 line of context).

    A model reading test output needs the failures and the summary, not the
    2,000 lines of dots.
    """
    lines = text.split("\n")
    n = len(lines)
    if n <= max_lines:
        return text
    keep = set(range(min(head, n))) | set(range(max(0, n - tail), n))
    for i, l in enumerate(lines):
        if INTERESTING.search(l):
            keep.update((i - 1, i, i + 1))
    keep = {i for i in keep if 0 <= i < n}
    out, omitted, last = [], 0, -1
    for i in range(n):
        if i in keep:
            if omitted:
                out.append(f"… [{omitted} lines omitted]")
                omitted = 0
            out.append(lines[i])
        else:
            omitted += 1
    if omitted:
        out.append(f"… [{omitted} lines omitted]")
    return "\n".join(out)


def level1(text: str) -> str:
    return dedupe(drop_progress(text), fuzzy=False)


def level2(text: str) -> str:
    return dedupe(shorten_ids(strip_timestamps(drop_progress(text))), fuzzy=True)


def level3(text: str, **kw) -> str:
    return smart_truncate(level2(text), **kw)
