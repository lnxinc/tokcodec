import ast
import json

from tokcodec import encode
from tokcodec.transforms import code, jsonx, logs, text as T


def test_lossless_text_is_meaning_preserving():
    s = "a  \n\x1b[31mred\x1b[0m\r\n\n\n\nb\t\n"
    assert T.lossless(s) == "a\nred\n\nb\n"


def test_shrink_indent_keeps_python_valid():
    src = "def f(x):\n    if x:\n        return [\n            1,\n        ]\n    return 0\n"
    out = T.shrink_indent(src)
    assert out.startswith("def f(x):\n if x:\n  return [\n")
    ast.parse(out)


def test_json_minify_roundtrips():
    s = json.dumps({"a": [1, 2, {"b": "c"}]}, indent=4)
    assert json.loads(jsonx.minify(s)) == json.loads(s)


def test_json_sample_stays_valid_json():
    s = json.dumps({"items": list(range(100)), "blob": "x" * 1000})
    out = json.loads(jsonx.sample(s, max_items=3, max_str=10))
    assert len(out["items"]) == 4 and out["items"][-1].startswith("…+97")
    assert out["blob"].startswith("xxxxxxxxxx…")


def test_log_dedupe_exact_and_fuzzy():
    s = "a\na\na\nb 1\nb 2\nc\n"
    assert logs.dedupe(s, fuzzy=False) == "a  [×3]\nb 1\nb 2\nc\n"
    assert logs.dedupe(s, fuzzy=True) == "a  [×3]\nb 1  [×2]\nc\n"


def test_log_smart_truncate_keeps_errors():
    lines = [f"ok {i}" for i in range(1000)]
    lines[500] = "ERROR something broke"
    out = logs.smart_truncate("\n".join(lines), head=5, tail=5, max_lines=50)
    assert "ERROR something broke" in out
    assert "ok 499" in out and "ok 501" in out  # context lines
    assert "lines omitted" in out
    assert out.count("\n") < 40


def test_py_skeleton_keeps_signatures_drops_bodies():
    src = '''import os

class A:
    """Doc."""

    def m(self, x: int) -> int:
        """Return x squared.

        Long explanation.
        """
        y = x * x
        return y

def g(): return 1

@dec
def h(
    a,
    b,
):
    if a:
        return b
    return a
'''
    out = code.py_skeleton(src)
    ast.parse(out)
    assert "def m(self, x: int) -> int:" in out
    assert '"""Return x squared."""' in out
    assert "y = x * x" not in out
    assert "def g(): return 1" in out
    assert "...  # 3 lines" in out


def test_py_strip_comments_and_docstrings():
    src = 'x = 1  # trailing\n# full line\ndef f():\n    """only doc"""\ns = "# not a comment"\n'
    out = code.py_strip_comments(code.py_strip_docstrings(src))
    ast.parse(out)
    assert "#" not in out.replace('"# not a comment"', "")
    assert '"# not a comment"' in out
    assert "pass" in out


def test_js_skeleton_and_comments():
    src = '''// header
import x from "y";
export function foo(a, b) {
  const s = "}"; // tricky
  /* block
     comment */
  return a + b;
}
const bar = async (q) => {
  await q();
  return 1;
};
class C {
  method(x) {
    if (x) {
      return 1;
    }
    return 2;
  }
}
'''
    sk = code.js_skeleton(src)
    assert "export function foo(a, b) { /* … 5 lines */ }" in sk
    assert "const bar = async (q) => { /* … 3 lines */ };" in sk
    assert "method(x) { /* … 5 lines */ }" in sk
    nc = code.js_strip_comments(src)
    assert "header" not in nc and "tricky" not in nc and 'const s = "}";' in nc


def test_pipeline_levels_monotonic_on_log():
    raw = "\n".join(f"2026-01-01T00:00:{i%60:02d} INFO step {i} done" for i in range(500))
    t = [encode(raw, level=l, kind="log").tokens_after for l in (0, 1, 2, 3)]
    assert t[0] >= t[1] >= t[2] >= t[3]
    assert t[3] < t[0] * 0.2


def test_level0_is_identity():
    raw = "  hello \n\n\n world"
    r = encode(raw, level=0)
    assert r.encoded == raw and r.tokens_before == r.tokens_after
