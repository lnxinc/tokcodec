"""Level-based encoding pipeline.

Level 0  raw
Level 1  LOSSLESS   ansi/CR/trailing-ws/blank lines, JSON minify, exact-dup log lines
Level 2  LIGHT      + timestamps/ids/fuzzy-dup in logs, comments+docstrings out of code
Level 3  HEAVY      + code skeleton (bodies dropped, indent shrunk), log smart-truncate,
                    JSON array/string sampling
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .count import count_tokens
from .detect import detect
from .transforms import code, jsonx, logs, text as T


@dataclass
class Result:
    kind: str
    level: int
    original: str
    encoded: str
    tokens_before: int = 0
    tokens_after: int = 0
    steps: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return (self.tokens_after / self.tokens_before) if self.tokens_before else 1.0

    @property
    def saved_pct(self) -> float:
        return (1 - self.ratio) * 100


def encode(
    raw: str,
    level: int = 2,
    kind: str = "auto",
    path: str | None = None,
    exact: bool = False,
    count: bool = True,
    **opts,
) -> Result:
    k = detect(raw, path, kind)
    steps: list[str] = []
    out = raw

    def step(name, fn, *a, **kw):
        nonlocal out
        before = out
        out = fn(out, *a, **kw)
        if out != before:
            steps.append(name)

    if level >= 1:
        step("lossless-text", T.lossless)
        if k == "json":
            step("json-minify", jsonx.minify)
        elif k == "log":
            step("log-dedupe", logs.level1)

    if level >= 2:
        if k == "log":
            step("log-fuzzy", logs.level2)
        elif k in ("python", "js"):
            step("strip-comments", code.strip_comments, k)
            step("lossless-text", T.lossless)
        elif k == "text":
            pass  # prose: nothing safe to remove beyond level 1

    if level >= 3:
        if k == "log":
            step("log-truncate", logs.smart_truncate,
                 head=opts.get("head", 40), tail=opts.get("tail", 60),
                 max_lines=opts.get("max_lines", 200))
        elif k in ("python", "js"):
            # skeleton needs original line numbers; rebuild from raw
            out, steps[:] = raw, []
            step("strip-comments", code.strip_comments_only, k)
            step("skeleton", code.skeleton, k)
            step("lossless-text", T.lossless)
            step("shrink-indent", T.shrink_indent)
        elif k == "json":
            step("json-sample", jsonx.sample,
                 max_items=opts.get("max_items", 8), max_str=opts.get("max_str", 200))

    r = Result(kind=k, level=level, original=raw, encoded=out, steps=steps)
    if count:
        r.tokens_before = count_tokens(raw, exact)
        r.tokens_after = count_tokens(out, exact)
    return r
