#!/usr/bin/env python3
"""Fidelity benchmark: does a model still answer questions correctly from
tokcodec-compressed input, and where exactly does each level break?

    uv run --extra bench python bench/fidelity/run.py --dry-run     # validate questions, no API calls
    uv run --extra bench python bench/fidelity/run.py --estimate    # token/cost estimate, no API calls
    uv run --extra bench python bench/fidelity/run.py               # run (asks before spending > $5)
    uv run --extra bench python bench/fidelity/run.py --levels 0 3 --samples pytest_run.log

Needs ANTHROPIC_API_KEY (or an `ant auth login` profile). Responses are cached
in bench/fidelity/.cache/ by content hash, so reruns are free. Output:
bench/FIDELITY.md (matrix + every wrong answer, unedited).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tokcodec import encode  # noqa: E402
from tokcodec.count import count_tokens  # noqa: E402

HERE = Path(__file__).parent
QDIR = HERE / "questions"
CACHE = HERE / ".cache"
SAMPLES = ROOT / "samples"

PRICES = {  # $ per million tokens, input/output
    "claude-sonnet-5": (2.0, 10.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

ANSWER_SYSTEM = (
    "You answer questions about a file. Answer using ONLY the file content provided. "
    "Be brief: give the exact name, signature, value, or line requested, nothing else. "
    "If the information is not present in the provided content, reply exactly: NOT IN FILE"
)
GRADE_SYSTEM = (
    "You are grading a short answer against an expected answer. Reply with exactly one word: "
    "CORRECT if the answer conveys the same fact as the expected answer (whitespace, quoting, "
    "and minor formatting differences do not matter), otherwise INCORRECT. "
    "An answer of NOT IN FILE is INCORRECT."
)


def load_questions(only: set[str] | None):
    qs = []
    for f in sorted(QDIR.glob("*.yaml")):
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
        if only and d["sample"] not in only:
            continue
        for q in d["questions"]:
            for k in ("id", "type", "question", "expected", "level_expected_to_answer"):
                assert k in q, f"{f.name}: question missing {k}: {q}"
            assert q["level_expected_to_answer"] in (1, 2, 3), f"{f.name}: bad level in {q['id']}"
            qs.append({**q, "sample": d["sample"]})
    return qs


def variants(sample: str, levels):
    raw = (SAMPLES / sample).read_text(encoding="utf-8")
    out = {}
    for l in levels:
        r = encode(raw, level=l, path=str(SAMPLES / sample))
        out[l] = (r.encoded, r.tokens_after)
    return out


def _client():
    import anthropic
    return anthropic.Anthropic()


def cached_call(client, model: str, system: str, user: str, max_tokens: int) -> str:
    key = hashlib.sha256(f"{model}\n{system}\n{user}".encode()).hexdigest()
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))["text"]
    r = client.messages.create(model=model, max_tokens=max_tokens, system=system,
                               messages=[{"role": "user", "content": user}])
    text = "".join(b.text for b in r.content if b.type == "text").strip()
    f.write_text(json.dumps({"text": text, "usage": r.usage.to_dict()}), encoding="utf-8")
    return text


def grade(client, model, expected: str, answer: str) -> bool:
    e, a = expected.strip().lower(), answer.strip().lower()
    if a == "not in file":
        return False
    if e in a or a in e and len(a) > 3:
        return True
    verdict = cached_call(client, model, GRADE_SYSTEM,
                          f"Expected: {expected}\nAnswer: {answer}", max_tokens=5)
    return verdict.upper().startswith("CORRECT")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--levels", nargs="+", type=int, default=[0, 1, 2, 3])
    ap.add_argument("--samples", nargs="*", help="restrict to these sample filenames")
    ap.add_argument("--dry-run", action="store_true", help="validate questions only")
    ap.add_argument("--estimate", action="store_true", help="print cost estimate and exit")
    ap.add_argument("--yes", action="store_true", help="don't ask before spending")
    a = ap.parse_args()

    qs = load_questions(set(a.samples) if a.samples else None)
    samples = sorted({q["sample"] for q in qs})
    print(f"{len(qs)} questions across {len(samples)} samples, levels {a.levels}")
    if a.dry_run:
        by = defaultdict(int)
        for q in qs:
            by[(q["type"], q["level_expected_to_answer"])] += 1
        for (t, l), n in sorted(by.items()):
            print(f"  {t:<11} expected to survive up to L{l}: {n}")
        return 0

    var = {s: variants(s, a.levels) for s in samples}
    in_tokens = sum(var[q["sample"]][l][1] + count_tokens(q["question"]) + 60
                    for q in qs for l in a.levels)
    calls = len(qs) * len(a.levels)
    pin, pout = PRICES.get(a.model, (5.0, 25.0))
    est = in_tokens / 1e6 * pin + calls * 40 / 1e6 * pout + calls * 0.5 * 80 / 1e6 * pin
    print(f"~{calls} answer calls, ~{in_tokens:,} input tokens, estimated ${est:.2f} on {a.model} (cache hits are free)")
    if a.estimate:
        return 0
    if est > 5 and not a.yes:
        if input("continue? [y/N] ").strip().lower() != "y":
            return 1

    client = _client()
    results = []  # (question, level, answer, correct)
    for i, q in enumerate(qs, 1):
        for l in a.levels:
            content, _ = var[q["sample"]][l]
            user = f"<file name=\"{q['sample']}\">\n{content}\n</file>\n\nQuestion: {q['question']}"
            ans = cached_call(client, a.model, ANSWER_SYSTEM, user, max_tokens=200)
            ok = grade(client, a.model, q["expected"], ans)
            results.append((q, l, ans, ok))
        print(f"\r{i}/{len(qs)} {q['id']:<20}", end="", file=sys.stderr)
    print(file=sys.stderr)
    write_report(a, qs, samples, var, results)
    return 0


def write_report(a, qs, samples, var, results):
    levels = a.levels
    acc = defaultdict(lambda: [0, 0])          # (type, level) -> [correct, total]
    acc_s = defaultdict(lambda: [0, 0])        # (sample, level)
    exp = defaultdict(lambda: [0, 0])          # level -> [correct among expected-to-survive, total]
    for q, l, ans, ok in results:
        acc[(q["type"], l)][0] += ok; acc[(q["type"], l)][1] += 1
        acc_s[(q["sample"], l)][0] += ok; acc_s[(q["sample"], l)][1] += 1
        if l == 0 or l <= q["level_expected_to_answer"]:
            exp[l][0] += ok; exp[l][1] += 1
    pct = lambda c, t: f"{100 * c / t:.0f}%" if t else "-"
    L = [f"# Fidelity results\n\nGenerated {dt.date.today().isoformat()} by `bench/fidelity/run.py`. "
         f"Model: `{a.model}`. {len(qs)} questions, {len(samples)} samples, levels {levels}.\n",
         "Every question is answered from the file at each level and graded against an expected answer "
         "(exact/substring match first, model-graded otherwise). `expected to survive` counts only questions "
         "whose answer should still be present at that level; the gap between the two rows is what compression "
         "deliberately removes.\n",
         "## Accuracy by level\n", "| | " + " | ".join(f"L{l}" for l in levels) + " |", "|---|" + "---:|" * len(levels)]
    L.append("| all questions | " + " | ".join(pct(*[sum(acc[(t, l)][i] for t in {q['type'] for q in qs}) for i in (0, 1)]) for l in levels) + " |")
    L.append("| expected to survive | " + " | ".join(pct(*exp[l]) for l in levels) + " |")
    tok = {l: sum(var[s][l][1] for s in samples) for l in levels}
    L.append("| input tokens (all samples) | " + " | ".join(f"{tok[l]:,}" for l in levels) + " |")
    L += ["", "## Accuracy by question type\n", "| type | " + " | ".join(f"L{l}" for l in levels) + " |", "|---|" + "---:|" * len(levels)]
    for t in sorted({q["type"] for q in qs}):
        L.append(f"| {t} | " + " | ".join(pct(*acc[(t, l)]) for l in levels) + " |")
    L += ["", "## Accuracy by sample\n", "| sample | " + " | ".join(f"L{l}" for l in levels) + " |", "|---|" + "---:|" * len(levels)]
    for s in samples:
        L.append(f"| `{s}` | " + " | ".join(pct(*acc_s[(s, l)]) for l in levels) + " |")
    wrong = [(q, l, ans) for q, l, ans, ok in results if not ok]
    L += ["", f"## Every wrong answer ({len(wrong)})\n",
          "Unedited. `exp L` is the highest level the question was expected to survive.\n",
          "| id | level | exp L | question | expected | answer |", "|---|---|---|---|---|---|"]
    for q, l, ans in wrong:
        esc = lambda x: str(x).replace("|", "\\|").replace("\n", " ")[:160]
        L.append(f"| {q['id']} | L{l} | {q['level_expected_to_answer']} | {esc(q['question'])} | `{esc(q['expected'])}` | {esc(ans)} |")
    (ROOT / "bench" / "FIDELITY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote bench/FIDELITY.md ({len(wrong)} wrong answers)")


if __name__ == "__main__":
    sys.exit(main())
