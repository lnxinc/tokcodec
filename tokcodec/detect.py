"""Guess what kind of content we're looking at so the right codec runs."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .langs import EXT_TO_LANG, FILE_TO_LANG, LANGS

_LOG_LINE = re.compile(
    r"^(\x1b\[[0-9;]*m)?\s*(\[?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\[?\d{2}:\d{2}:\d{2}|"
    r"(INFO|DEBUG|WARN(ING)?|ERROR|TRACE|FATAL)\b|npm (WARN|ERR|info|verb)|PASS|FAIL|"
    r"\d+ passed|=+ .* =+$|\S+/\S+\.py::)",
    re.I,
)
# cheap content sniffing for pasted snippets with no path
_SNIFF = [
    ("python", re.compile(r"^(def |class \w+.*:|import \w|from \S+ import )", re.M), 3),
    ("go", re.compile(r"^(package \w+|func |import \()", re.M), 2),
    ("rust", re.compile(r"^(pub |fn |use |impl |struct |enum )", re.M), 3),
    ("java", re.compile(r"^(package [\w.]+;|import [\w.]+;|public (class|interface|enum) )", re.M), 2),
    ("ruby", re.compile(r"^(require |module |class \w+|def \w+|\s*end$)", re.M), 3),
    ("js", re.compile(r"^(import .* from |export |const |function |class )", re.M), 3),
    ("php", re.compile(r"^<\?php|^(namespace|use) [\w\\]+;", re.M), 1),
    ("markup", re.compile(r"^\s*<(!DOCTYPE|html|svg|\?xml)", re.I | re.M), 1),
]


def detect(text: str, path: str | None = None, kind: str | None = None) -> str:
    if kind and kind != "auto":
        if kind not in LANGS:
            raise ValueError(f"unknown kind {kind!r}; one of: {', '.join(LANGS)}")
        return kind
    if path:
        p = Path(path)
        k = FILE_TO_LANG.get(p.name) or EXT_TO_LANG.get(p.suffix.lower())
        if k:
            return k
    s = text.lstrip()
    if s[:1] in "{[":
        try:
            json.loads(text)
            return "json"
        except ValueError:
            pass
    if s.startswith(("diff --git", "--- ", "Index: ")):
        return "diff"
    lines = text.splitlines()[:200]
    if lines:
        logish = sum(1 for l in lines if _LOG_LINE.search(l))
        if logish / len(lines) > 0.3:
            return "log"
    for name, rx, need in _SNIFF:
        if len(rx.findall(text)) >= need:
            return name
    return "text"
