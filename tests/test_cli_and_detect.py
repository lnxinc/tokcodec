import json
import subprocess
import sys
from pathlib import Path

import pytest

from tokcodec.detect import detect

SAMPLES = Path(__file__).parent.parent / "samples"


@pytest.mark.parametrize(
    "text,path,expected",
    [
        ('{"a": 1}', None, "json"),
        ("[1,2,3]", None, "json"),
        ("diff --git a/x b/x\n--- a/x\n+++ b/x\n", None, "diff"),
        ("import os\nimport sys\n\ndef f():\n    pass\nclass A: pass\n", None, "python"),
        ("import a from 'a';\nexport const x = 1;\nexport function f() {}\n", None, "js"),
        ("\n".join(f"2026-01-01T00:00:00 INFO line {i}" for i in range(10)), None, "log"),
        ("Just some prose.\n\nAnother paragraph.", None, "text"),
        ("anything", "foo.py", "python"),
        ("anything", "foo.tsx", "js"),
        ("anything", "foo.log", "log"),
        ("anything", "foo.md", "text"),
    ],
)
def test_detect(text, path, expected):
    assert detect(text, path) == expected


def test_detect_explicit_kind_wins():
    assert detect("{}", "x.py", kind="log") == "log"


def run(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "tokcodec.cli", *args],
        input=stdin, capture_output=True, text=True, check=True,
    )


def test_cli_shorthand_and_stats():
    r = run(str(SAMPLES / "pytest_run.log"), "-l", "2", "-s")
    assert "1 failed, 411 passed" in r.stdout
    assert "AssertionError" in r.stdout
    assert "[tokcodec kind=log level=2" in r.stderr


def test_cli_stdin_json_minify():
    r = run("-", "-l", "1", "-k", "json", stdin=json.dumps({"a": [1, 2]}, indent=2))
    assert r.stdout.strip() == '{"a":[1,2]}'


def test_cli_level0_passthrough():
    r = run("-", "-l", "0", stdin="  keep   me  \n")
    assert r.stdout == "  keep   me  \n"


def test_cli_count():
    r = run("count", "-", stdin="hello world")
    assert r.stdout.strip().isdigit()


def test_cli_bench_runs_on_samples():
    r = run("bench", str(SAMPLES))
    assert "TOTAL" in r.stdout and "pytest_run.log" in r.stdout


def test_cli_why_runs():
    r = run("why", str(SAMPLES / "decoder.py"))
    assert "gzip+base64" in r.stdout and "tokcodec L3" in r.stdout


def test_every_sample_gets_smaller_at_level3_and_stays_parseable():
    from tokcodec import encode
    import ast

    for f in SAMPLES.iterdir():
        if f.suffix == ".md":
            continue
        raw = f.read_text()
        r = encode(raw, level=3, path=str(f))
        # dense files (short bodies, long signatures) shrink less; 0.65 still means a real outline
        assert r.tokens_after < r.tokens_before * 0.65, f.name
        if f.suffix == ".py":
            ast.parse(r.encoded)  # skeleton is still valid Python
        if f.suffix == ".json":
            json.loads(r.encoded)  # sampled JSON is still valid JSON
