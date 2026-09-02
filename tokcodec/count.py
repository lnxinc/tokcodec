"""Token counting.

Claude's tokenizer is not published. Two modes:

* proxy (default): tiktoken `o200k_base`. Same family of BPE tokenizer, so the
  *ratio* before/after is reliable even when absolute counts drift by 10-30%.
* exact (--exact): Anthropic `messages.count_tokens`. Needs credentials
  (ANTHROPIC_API_KEY or an `ant auth login` profile). Costs no money.
"""
from __future__ import annotations

import functools

EXACT_MODEL = "claude-opus-5"


@functools.lru_cache(maxsize=1)
def _enc():
    import tiktoken

    return tiktoken.get_encoding("o200k_base")


def count_proxy(text: str) -> int:
    if not text:
        return 0
    return len(_enc().encode(text, disallowed_special=()))


def count_exact(text: str, model: str = EXACT_MODEL) -> int:
    import anthropic

    client = anthropic.Anthropic()
    r = client.messages.count_tokens(
        model=model, messages=[{"role": "user", "content": text or " "}]
    )
    return r.input_tokens


def count_tokens(text: str, exact: bool = False) -> int:
    return count_exact(text) if exact else count_proxy(text)
