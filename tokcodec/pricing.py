"""Input-token prices ($ per million) used for --cost. Update when Anthropic's price list changes."""
PRICES_PER_MTOK = {
    "claude-opus-5": 5.00,
    "claude-sonnet-5": 2.00,
    "claude-haiku-4-5": 1.00,
}


def cost(tokens: int, model: str) -> float:
    return tokens / 1e6 * PRICES_PER_MTOK[model]


def cost_line(before: int, after: int) -> str:
    parts = []
    for m, p in PRICES_PER_MTOK.items():
        parts.append(f"{m.split('-', 1)[1]}: ${cost(before, m):.4f}→${cost(after, m):.4f}")
    return "  ".join(parts)
