"""JSON codec. Pretty-printed JSON is ~30-50% whitespace tokens."""
from __future__ import annotations

import json
from typing import Any


def minify(text: str) -> str:
    try:
        obj = json.loads(text)
    except ValueError:
        return text
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _sample(obj: Any, max_items: int, max_str: int) -> Any:
    if isinstance(obj, list):
        if len(obj) > max_items:
            keep = [_sample(x, max_items, max_str) for x in obj[:max_items]]
            return keep + [f"…+{len(obj) - max_items} more items"]
        return [_sample(x, max_items, max_str) for x in obj]
    if isinstance(obj, dict):
        return {k: _sample(v, max_items, max_str) for k, v in obj.items()}
    if isinstance(obj, str) and len(obj) > max_str:
        return obj[:max_str] + f"…(+{len(obj) - max_str} chars)"
    return obj


def sample(text: str, max_items: int = 8, max_str: int = 200) -> str:
    """Lossy: cap arrays at max_items and long strings at max_str. Stays valid JSON."""
    try:
        obj = json.loads(text)
    except ValueError:
        return text
    return json.dumps(_sample(obj, max_items, max_str), separators=(",", ":"), ensure_ascii=False)
