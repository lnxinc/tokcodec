"""Guess what kind of content we're looking at so the right codec runs."""
from __future__ import annotations

import json
import re
from pathlib import Path

EXT = {
    ".py": "python",
    ".js": "js", ".jsx": "js", ".ts": "js", ".tsx": "js", ".mjs": "js", ".cjs": "js",
    ".json": "json",
    ".log": "log", ".txt": "text",
    ".md": "text", ".rst": "text",
    ".diff": "diff", ".patch": "diff",
}

_LOG_LINE = re.compile(
    r"^(\x1b\[[0-9;]*m)?\s*(\[?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\[?\d{2}:\d{2}:\d{2}|"
    r"(INFO|DEBUG|WARN(ING)?|ERROR|TRACE|FATAL)\b|npm (WARN|ERR|info|verb)|PASS|FAIL|"
    r"\d+ passed|=+ .* =+$|\S+/\S+\.py::)",
    re.I,
)
_CODE_PY = re.compile(r"^(def |class |import |from \S+ import )", re.M)
_CODE_JS = re.compile(r"^(import .* from |export |const |function |class )", re.M)


def detect(text: str, path: str | None = None, kind: str | None = None) -> str:
    if kind and kind != "auto":
        return kind
    if path:
        k = EXT.get(Path(path).suffix.lower())
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
    if len(_CODE_PY.findall(text)) >= 3:
        return "python"
    if len(_CODE_JS.findall(text)) >= 3:
        return "js"
    return "text"
