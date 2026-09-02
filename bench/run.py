#!/usr/bin/env python3
"""Reproducible benchmark. Writes bench/RESULTS.md and refreshes the table in README.md.

    uv run python bench/run.py            # proxy tokenizer (tiktoken o200k_base)
    uv run python bench/run.py --exact    # Anthropic count_tokens (needs credentials) -> bench/RESULTS-exact.md
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tokcodec import encode  # noqa: E402
from tokcodec.count import count_tokens  # noqa: E402

SAMPLES = ROOT / "samples"
DESC = {
    "pytest_run.log": "pytest run, 412 tests, ANSI colour, timestamps, 1 failure",
    "api_response.json": "pretty-printed REST response, 120 records",
    "argparse.py": "CPython stdlib `argparse.py`",
    "decoder.py": "CPython stdlib `json/decoder.py`",
    "npm_module.js": "`glob/dist/esm/walker.js` from npm",
    "strings_builder.go": "Go stdlib `strings/builder.go`",
    "vec_deque_iter.rs": "Rust `alloc` `vec_deque/iter.rs`",
    "Joiner.java": "Guava `Joiner.java`",
    "LinkedList.cs": ".NET runtime `LinkedList.cs`",
    "Strings.kt": "Kotlin stdlib `text/Strings.kt`",
    "linkhash.h": "json-c `linkhash.h`",
    "set.rb": "Ruby stdlib `set.rb`",
    "Arr.php": "Laravel `Collections/Arr.php`",
}


def pct(a: int, b: int) -> str:
    return f"−{(1 - b / a) * 100:.0f}%" if a else "n/a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exact", action="store_true")
    a = ap.parse_args()

    rows, tot = [], [0, 0, 0, 0]
    for f in sorted(SAMPLES.iterdir()):
        if f.suffix == ".md":
            continue
        raw = f.read_text(encoding="utf-8")
        rs = [encode(raw, level=l, path=str(f), exact=a.exact) for l in (1, 2, 3)]
        base = rs[0].tokens_before
        tot[0] += base
        for i, r in enumerate(rs):
            tot[i + 1] += r.tokens_after
        rows.append((f.name, rs[0].kind, DESC.get(f.name, ""), base, [r.tokens_after for r in rs]))

    counter = "Anthropic `count_tokens` (exact)" if a.exact else "tiktoken `o200k_base` (proxy)"
    md = ["| file | kind | what it is | raw tokens | L1 lossless | L2 light | L3 heavy |",
          "|---|---|---|---:|---:|---:|---:|"]
    for name, kind, desc, base, ls in rows:
        cells = [f"{t:,} ({pct(base, t)})" for t in ls]
        md.append(f"| `{name}` | {kind} | {desc} | {base:,} | {' | '.join(cells)} |")
    b = tot[0]
    md.append(f"| **total** | | | **{b:,}** | **{tot[1]:,} ({pct(b, tot[1])})** | "
              f"**{tot[2]:,} ({pct(b, tot[2])})** | **{tot[3]:,} ({pct(b, tot[3])})** |")
    table = "\n".join(md)

    # why table
    src = (SAMPLES / "decoder.py").read_text(encoding="utf-8")
    base = count_tokens(src, a.exact)
    why_rows = [
        ("original", src, "yes"),
        ("gzip + base64", base64.b64encode(gzip.compress(src.encode(), mtime=0)).decode(), "no, the model cannot inflate gzip"),
        ("vowels removed", re.sub(r"(?<=\w)[aeiou]", "", src), "partly, and it guesses wrong"),
        ("tokcodec L1", encode(src, 1, count=False).encoded, "yes, lossless"),
        ("tokcodec L2", encode(src, 2, count=False).encoded, "yes, comments gone"),
        ("tokcodec L3", encode(src, 3, count=False).encoded, "yes, bodies gone (outline)"),
    ]
    why = ["| variant | bytes | tokens | vs original | model can read it? |", "|---|---:|---:|---:|---|"]
    for name, v, note in why_rows:
        t = count_tokens(v, a.exact)
        why.append(f"| {name} | {len(v.encode()):,} | {t:,} | {(t / base - 1) * 100:+.0f}% | {note} |")
    why_table = "\n".join(why)

    stamp = dt.date.today().isoformat()
    results = (f"# Benchmark results\n\nGenerated {stamp} by `bench/run.py`. Counter: {counter}.\n\n"
               f"## Savings per level\n\n{table}\n\n## Bytes are not tokens\n\n"
               f"Measured on `samples/decoder.py`.\n\n{why_table}\n")
    if a.exact:
        # exact counts go to their own file; README/RESULTS.md stay on the proxy so anyone can regenerate them
        results = results.replace("# Benchmark results", "# Benchmark results (exact Claude token counts)", 1)
        (ROOT / "bench" / "RESULTS-exact.md").write_text(results, encoding="utf-8")
        print(results)
        return 0
    (ROOT / "bench" / "RESULTS.md").write_text(results, encoding="utf-8")

    readme = ROOT / "README.md"
    if readme.exists():
        s = readme.read_text(encoding="utf-8")
        s = re.sub(r"(<!-- BENCH -->\n).*?(\n<!-- /BENCH -->)", lambda m: m.group(1) + table + m.group(2), s, flags=re.S)
        s = re.sub(r"(<!-- WHY -->\n).*?(\n<!-- /WHY -->)", lambda m: m.group(1) + why_table + m.group(2), s, flags=re.S)
        readme.write_text(s, encoding="utf-8")
    print(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
