"""Lossless-for-meaning text transforms. Safe at every level."""
from __future__ import annotations

import re

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\r(?!\n)")
TRAILING_WS = re.compile(r"[ \t]+$", re.M)
MANY_BLANKS = re.compile(r"\n{3,}")
CR = re.compile(r"\r\n?")


def strip_ansi(text: str) -> str:
    return ANSI.sub("", text)


def normalize_newlines(text: str) -> str:
    return CR.sub("\n", text)


def strip_trailing_ws(text: str) -> str:
    return TRAILING_WS.sub("", text)


def collapse_blank_lines(text: str, keep: int = 1) -> str:
    return MANY_BLANKS.sub("\n" * (keep + 1), text)


def shrink_indent(text: str, unit: int | None = None, to: str = " ") -> str:
    """Rewrite indentation so one level == `to` (default: a single space).

    Structure is preserved exactly (each level maps to one unit), so Python
    stays valid. Detects the indent unit from the file when not given.
    """
    lines = text.split("\n")
    if unit is None:
        widths = sorted(
            {len(l) - len(l.lstrip(" ")) for l in lines if l.strip() and l.startswith(" ")}
        )
        unit = widths[0] if widths else 0
        # prefer 4/2 if they divide all seen widths
        for cand in (4, 2):
            if widths and all(w % cand == 0 for w in widths):
                unit = cand
                break
    out = []
    for l in lines:
        if not l.strip():
            out.append("")
            continue
        stripped = l.lstrip(" \t")
        lead = l[: len(l) - len(stripped)]
        levels = lead.count("\t") + ((lead.count(" ") // unit) if unit else 0)
        out.append(to * levels + stripped)
    return "\n".join(out)


def lossless(text: str) -> str:
    text = normalize_newlines(text)
    text = strip_ansi(text)
    text = strip_trailing_ws(text)
    text = collapse_blank_lines(text)
    if not text.strip():
        return ""
    nl = "\n" if text.endswith("\n") else ""
    return text.strip("\n") + nl
