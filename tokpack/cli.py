"""tokpack CLI.

  tokpack FILE [-l 0..3] [--kind K] [--stats] [--exact]   encode one file (or - for stdin)
  tokpack bench PATH... [--exact]                          table of savings per level
  tokpack count FILE                                        token count
  tokpack why                                               show why gzip/abbreviation backfire
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .count import count_tokens
from .pipeline import encode


def _read(p: str) -> str:
    if p == "-":
        return sys.stdin.read()
    return Path(p).read_text(errors="replace")


def cmd_encode(a):
    raw = _read(a.file)
    r = encode(raw, level=a.level, kind=a.kind, path=None if a.file == "-" else a.file,
               exact=a.exact, head=a.head, tail=a.tail, max_lines=a.max_lines)
    sys.stdout.write(r.encoded)
    if not r.encoded.endswith("\n"):
        sys.stdout.write("\n")
    if a.stats:
        print(f"[tokpack kind={r.kind} level={r.level} {r.tokens_before}→{r.tokens_after} tok "
              f"(-{r.saved_pct:.0f}%) steps={','.join(r.steps) or 'none'}]", file=sys.stderr)


def _iter_files(paths):
    for p in paths:
        p = Path(p)
        if p.is_dir():
            yield from (f for f in sorted(p.rglob("*")) if f.is_file() and not f.name.startswith("."))
        else:
            yield p


def cmd_bench(a):
    rows = []
    tot = [0, 0, 0, 0]
    for f in _iter_files(a.paths):
        try:
            raw = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        rs = [encode(raw, level=l, path=str(f), exact=a.exact) for l in (1, 2, 3)]
        base = rs[0].tokens_before
        tot[0] += base
        for i, r in enumerate(rs):
            tot[i + 1] += r.tokens_after
        rows.append((f.name, rs[0].kind, base, *[r.tokens_after for r in rs]))
    w = max(len(r[0]) for r in rows) if rows else 10
    print(f"{'file':<{w}}  {'kind':<7}{'raw':>8}{'L1':>8}{'L2':>8}{'L3':>8}   L1     L2     L3")
    for name, kind, base, l1, l2, l3 in rows:
        pct = lambda x: f"-{(1 - x / base) * 100:3.0f}%" if base else "  n/a"
        print(f"{name:<{w}}  {kind:<7}{base:>8}{l1:>8}{l2:>8}{l3:>8}   {pct(l1)}  {pct(l2)}  {pct(l3)}")
    if rows:
        b = tot[0]
        print(f"{'TOTAL':<{w}}  {'':<7}{b:>8}{tot[1]:>8}{tot[2]:>8}{tot[3]:>8}   "
              f"-{(1 - tot[1] / b) * 100:3.0f}%  -{(1 - tot[2] / b) * 100:3.0f}%  -{(1 - tot[3] / b) * 100:3.0f}%")
    print(f"\ncounter: {'anthropic count_tokens (exact)' if a.exact else 'tiktoken o200k_base (proxy)'}")


def cmd_count(a):
    print(count_tokens(_read(a.file), exact=a.exact))


def cmd_why(a):
    import base64, gzip, zlib, re
    raw = _read(a.file) if a.file else (Path(__file__).parent / "pipeline.py").read_text()
    variants = {
        "original": raw,
        "gzip+base64": base64.b64encode(gzip.compress(raw.encode())).decode(),
        "zlib+base85": base64.b85encode(zlib.compress(raw.encode(), 9)).decode(),
        "drop vowels": re.sub(r"(?<=\w)[aeiou]", "", raw),
        "no spaces": re.sub(r"[ \t]+", " ", raw),
        "tokpack L1": encode(raw, 1, count=False).encoded,
        "tokpack L2": encode(raw, 2, count=False).encoded,
        "tokpack L3": encode(raw, 3, count=False).encoded,
    }
    base = count_tokens(raw, a.exact)
    print(f"{'variant':<14}{'bytes':>8}{'tokens':>8}{'vs orig':>9}   readable by the model?")
    notes = {
        "gzip+base64": "no - model can't inflate gzip",
        "zlib+base85": "no",
        "drop vowels": "partly - and it guesses wrong",
        "no spaces": "yes, but barely helps",
        "tokpack L1": "yes - lossless",
        "tokpack L2": "yes - loses comments/timestamps",
        "tokpack L3": "yes - loses bodies/details (overview)",
        "original": "yes",
    }
    for name, v in variants.items():
        t = count_tokens(v, a.exact)
        print(f"{name:<14}{len(v.encode()):>8}{t:>8}{(t / base - 1) * 100:>+8.0f}%   {notes[name]}")
    print("\nBytes and tokens are different currencies: byte compression produces high-entropy")
    print("text that the BPE tokenizer splits into ~1 token per 1-2 chars, and the model can't")
    print("decode it anyway. Token compression removes *information the reader doesn't need*.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tokpack", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd")

    def common(p):
        p.add_argument("--exact", action="store_true", help="count with Anthropic count_tokens (needs credentials)")

    e = sub.add_parser("encode", help="encode a file or stdin (-)")
    e.add_argument("file")
    e.add_argument("-l", "--level", type=int, default=2, choices=[0, 1, 2, 3])
    e.add_argument("-k", "--kind", default="auto", choices=["auto", "text", "log", "json", "python", "js", "diff"])
    e.add_argument("-s", "--stats", action="store_true", help="print token stats to stderr")
    e.add_argument("--head", type=int, default=40)
    e.add_argument("--tail", type=int, default=60)
    e.add_argument("--max-lines", type=int, default=200)
    common(e); e.set_defaults(fn=cmd_encode)

    b = sub.add_parser("bench", help="benchmark savings per level")
    b.add_argument("paths", nargs="+")
    common(b); b.set_defaults(fn=cmd_bench)

    c = sub.add_parser("count", help="count tokens")
    c.add_argument("file"); common(c); c.set_defaults(fn=cmd_count)

    w = sub.add_parser("why", help="show why classic compression backfires on tokens")
    w.add_argument("file", nargs="?"); common(w); w.set_defaults(fn=cmd_why)

    # allow `tokpack FILE` shorthand
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] not in {"encode", "bench", "count", "why", "-h", "--help", "--version"}:
        argv = ["encode", *argv]
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help(); return 0
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
