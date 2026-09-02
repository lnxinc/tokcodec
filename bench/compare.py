#!/usr/bin/env python3
"""Estimate (tiktoken proxy) vs actual (Anthropic count_tokens) from the two results files.
Writes bench/ESTIMATE-VS-ACTUAL.md and refreshes the <!-- COMPARE --> block in README.md.
No API calls: run bench/run.py and bench/run.py --exact first."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tokcodec.pricing import PRICES_PER_MTOK  # noqa: E402

ROW = re.compile(r"^\| `([^`]+)` \| (\w+) \| .*? \| ([\d,]+) \| ([\d,]+) \(.*?\) \| ([\d,]+) \(.*?\) \| ([\d,]+) \(.*?\) \|$")


def load(path: Path) -> dict[str, tuple[int, int, int, int]]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            out[m.group(1)] = tuple(int(x.replace(",", "")) for x in m.group(3, 4, 5, 6))
    return out


def main() -> int:
    est = load(ROOT / "bench" / "RESULTS.md")
    act = load(ROOT / "bench" / "RESULTS-exact.md")
    names = [n for n in est if n in act]
    if not names:
        print("need both bench/RESULTS.md and bench/RESULTS-exact.md", file=sys.stderr)
        return 1
    pct = lambda a, b: (1 - b / a) * 100
    rows = ["| file | estimate raw → L3 | actual raw → L3 | estimated saving | actual saving | estimate error |",
            "|---|---:|---:|---:|---:|---:|"]
    te = [0, 0]; ta = [0, 0]
    for n in names:
        e, a = est[n], act[n]
        te[0] += e[0]; te[1] += e[3]; ta[0] += a[0]; ta[1] += a[3]
        rows.append(f"| `{n}` | {e[0]:,} → {e[3]:,} | {a[0]:,} → {a[3]:,} | −{pct(e[0], e[3]):.0f}% | −{pct(a[0], a[3]):.0f}% | {pct(e[0], e[3]) - pct(a[0], a[3]):+.1f} pts |")
    rows.append(f"| **total** | **{te[0]:,} → {te[1]:,}** | **{ta[0]:,} → {ta[1]:,}** | **−{pct(*te):.0f}%** | **−{pct(*ta):.0f}%** | **{pct(*te) - pct(*ta):+.1f} pts** |")
    table = "\n".join(rows)
    ratio = ta[0] / te[0]

    # worked cost example on actual counts: one read of every sample, raw vs L3, per model
    cost_rows = ["| model | input price | read all 13 files raw | read them at level 3 | saved per pass | saved per 1,000 passes |",
                 "|---|---:|---:|---:|---:|---:|"]
    for m, p in PRICES_PER_MTOK.items():
        raw = ta[0] / 1e6 * p; l3 = ta[1] / 1e6 * p
        cost_rows.append(f"| {m} | ${p:.2f}/M | ${raw:.3f} | ${l3:.3f} | ${raw - l3:.3f} | ${(raw - l3) * 1000:,.0f} |")
    cost_table = "\n".join(cost_rows)

    body = (f"# Estimate vs actual\n\nEstimate: tiktoken `o200k_base`, what `tokcodec` prints by default. "
            f"Actual: Anthropic `count_tokens` for Claude Sonnet/Opus 5 (`--exact`). Level 3 on every sample.\n\n{table}\n\n"
            f"Claude's tokenizer counts **{ratio:.2f}×** the proxy's tokens on these files, so absolute estimates are low, "
            f"but the *saving* is what you decide on, and that is within a few points either way.\n\n"
            f"## What that is worth\n\nActual counts, one pass over all 13 samples ({ta[0]:,} tokens raw, {ta[1]:,} at level 3), "
            f"input price only, uncached:\n\n{cost_table}\n\n"
            "Cached reads are cheaper per token, but the context-window headroom saved is the same either way.\n")
    (ROOT / "bench" / "ESTIMATE-VS-ACTUAL.md").write_text(body, encoding="utf-8")

    readme = ROOT / "README.md"
    s = readme.read_text(encoding="utf-8")
    block = table + "\n\n" + cost_table
    s2 = re.sub(r"(<!-- COMPARE -->\n).*?(\n<!-- /COMPARE -->)", lambda m: m.group(1) + block + m.group(2), s, flags=re.S)
    if s2 != s:
        readme.write_text(s2, encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
