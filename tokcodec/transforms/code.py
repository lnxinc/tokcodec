"""Source-code codec.

Level 2: strip comments and docstrings (the model can usually infer intent from
names; keep them when you need the *why*).
Level 3: skeleton - keep imports, signatures, class layout, first docstring
line; drop function bodies. This is the "I-frame": enough to navigate and
decide what to read in full.

Python uses ast/tokenize. Brace languages (JS/TS, Go, Rust, Java, Kotlin, C#,
C/C++, Swift, Dart, Scala, PHP, Zig) share one scanner that tracks strings and
comments while matching braces. Ruby uses def…end by indentation.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize

from ..langs import LANGS


# ---------------------------------------------------------------- Python ----
def _docstring_ranges(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                yield body[0].lineno, body[0].end_lineno, len(body) == 1, body[0].col_offset


def py_strip_docstrings(text: str) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    lines = text.split("\n")
    for start, end, only_stmt, col in sorted(_docstring_ranges(tree), reverse=True):
        repl = [" " * col + "pass"] if only_stmt else []
        lines[start - 1:end] = repl
    return "\n".join(lines)


def py_strip_comments(text: str) -> str:
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return text
    lines = text.split("\n")
    comment_only: set[int] = set()
    for t in reversed(toks):  # reverse so column cuts don't shift earlier tokens
        if t.type == tokenize.COMMENT:
            row, col = t.start
            head = lines[row - 1][:col].rstrip()
            lines[row - 1] = head
            if not head.strip():
                comment_only.add(row - 1)
    return "\n".join(l for i, l in enumerate(lines) if i not in comment_only)


def py_skeleton(text: str, keep_docstring_line: bool = True) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    lines = text.split("\n")
    cuts: list[tuple[int, int, str]] = []  # (start_line0, end_line0 exclusive, replacement)

    def trim_doc(container):
        body = container.body
        if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                and isinstance(body[0].value.value, str) and body[0].end_lineno > body[0].lineno:
            first = body[0].value.value.strip().split("\n")[0]
            cuts.append((body[0].lineno - 1, body[0].end_lineno, f'{" " * body[0].col_offset}"""{first}"""'))

    def visit(container):
        trim_doc(container)
        for node in container.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                first = body[0]
                if first.lineno == node.lineno:  # one-liner def
                    continue
                keep_doc = (
                    keep_docstring_line and isinstance(first, ast.Expr)
                    and isinstance(getattr(first, "value", None), ast.Constant)
                    and isinstance(first.value.value, str)
                )
                indent = " " * first.col_offset
                start = first.lineno - 1
                end = node.end_lineno
                n = end - start
                marker = f"{indent}...  # {n} line{'s' if n != 1 else ''}"
                if keep_doc:
                    doc = first.value.value.strip().split("\n")[0]
                    cuts.append((start, end, f'{indent}"""{doc}"""\n{marker}'))
                else:
                    cuts.append((start, end, marker))
            elif isinstance(node, ast.ClassDef):
                visit(node)

    visit(tree)
    for start, end, repl in sorted(cuts, reverse=True):
        lines[start:end] = [repl]
    return "\n".join(lines)


# ------------------------------------------------------ generic scanner ----
def _scan(text: str, start: int, line_comment: tuple[str, ...], block: tuple[str, str] | None,
          quotes: str = "'\"`"):
    """Yield (index, char, in_code) from start, skipping strings and comments."""
    i, n = start, len(text)
    while i < n:
        c = text[i]
        lc = next((m for m in line_comment if text.startswith(m, i)), None)
        if lc:
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                yield k, text[k], False
            i = j
            continue
        if block and text.startswith(block[0], i):
            j = text.find(block[1], i + len(block[0]))
            j = n if j < 0 else j + len(block[1])
            for k in range(i, j):
                yield k, text[k], False
            i = j
            continue
        if c in quotes:
            q = c
            yield i, c, False
            i += 1
            while i < n and text[i] != q:
                if text[i] == "\\":
                    yield i, text[i], False
                    i += 1
                if i < n:
                    yield i, text[i], False
                i += 1
            if i < n:
                yield i, text[i], False
            i += 1
            continue
        yield i, c, True
        i += 1


_STYLE = {
    "c": (("//",), ("/*", "*/"), "'\"`"),
    "php": (("//", "#"), ("/*", "*/"), "'\""),
    "hash": (("#",), None, "'\""),
    "dash": (("--",), ("/*", "*/"), "'\""),
    "xml": ((), ("<!--", "-->"), ""),
}


def strip_comments_generic(text: str, style: str) -> str:
    line_comment, block, quotes = _STYLE[style]
    keep = []
    for _, ch, _in_code in _scan(text, 0, line_comment, block, quotes):
        keep.append(ch)
    # _scan yields comment chars too (in_code False); rebuild skipping them
    out = []
    i, n = 0, len(text)
    while i < n:
        lc = next((m for m in line_comment if text.startswith(m, i)), None)
        if lc == "#" and style == "php" and text.startswith("#[", i):
            lc = None
        if lc and (style != "hash" or i == 0 or text[i - 1] in " \t\n"):
            j = text.find("\n", i); i = n if j < 0 else j; continue
        if block and text.startswith(block[0], i):
            j = text.find(block[1], i + len(block[0])); i = n if j < 0 else j + len(block[1]); continue
        c = text[i]
        if c in quotes:
            q, j = c, i + 1
            while j < n and text[j] != q:
                if text[j] == "\n" and q != "`":
                    break  # unterminated single-line string: stop at EOL
                j += 2 if text[j] == "\\" else 1
            out.append(text[i:j + 1]); i = j + 1; continue
        out.append(c); i += 1
    res = "".join(out)
    return "\n".join(l.rstrip() for l in res.split("\n"))


def _matching_brace(text: str, open_idx: int, style: str) -> int:
    line_comment, block, quotes = _STYLE[style]
    depth = 0
    for i, ch, in_code in _scan(text, open_idx, line_comment, block, quotes):
        if not in_code:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


# A function/method header: something like `... name(params) ... {` at end of line,
# not a control statement, not a type declaration. Params may span lines; the
# `{` may sit on the next line (Allman style).
_CONTROL = r"(?:if|for|foreach|while|switch|catch|else|return|do|try|match|when|select|lock|synchronized|using|with|defer|go|new|throw|await|yield|guard|unsafe|loop|elif|until|unless|case)"
_TYPEDECL = r"(?:class|struct|interface|enum|object|impl|trait|namespace|record|union|protocol|extension|actor|module|type|typedef)"
# A function/method header: `... name(params) ... {` where `{` ends the line
# or sits alone on the next line (Allman). Params may span lines. Not a control
# statement, not a type declaration, no `=` before the name (that's an assignment).
_HEADER = re.compile(
    r"^[ \t]*"
    r"(?!" + _CONTROL + r"\b)"
    r"(?![^;={}()\n]*\b" + _TYPEDECL + r"\b)"
    r"(?![ \t]*[}\]\)])"
    r"[^;={}()\n]*?\b[\w$]+\s*(?:<[^{};()\n]*>)?\s*\(([^;{}]*?)\)[^;{}\n]*?(?:\n[ \t]*)?\{[ \t]*$"
    r"|^[ \t]*(?:export\s+)?(?:const|let|var)\s+[\w$]+\s*(?::[^=\n]+)?=\s*(?:async\s*)?(?:\([^)]*\)|[\w$]+)\s*(?::[^=\n]+)?=>\s*\{[ \t]*$",
    re.M,
)


def brace_skeleton(text: str, style: str = "c") -> str:
    pos = 0
    out = []
    while True:
        m = _HEADER.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        open_idx = text.index("{", m.start())
        close_idx = _matching_brace(text, open_idx, style)
        if close_idx < 0:
            out.append(text[pos:m.end()])
            pos = m.end()
            continue
        body = text[open_idx + 1:close_idx]
        n = body.count("\n")
        out.append(text[pos:open_idx + 1])
        if n >= 2:
            out.append(f" /* … {n} lines */ ")
        else:
            out.append(body)
        out.append("}")
        pos = close_idx + 1
    return "".join(out)


# ------------------------------------------------------------------ Ruby ----
_RB_DEF = re.compile(r"^([ \t]*)def\b")


def ruby_skeleton(text: str) -> str:
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    while i < n:
        m = _RB_DEF.match(lines[i])
        if not m or lines[i].rstrip().endswith((";", " end")) or " = " in lines[i].split("def", 1)[1] and "(" not in lines[i]:
            out.append(lines[i]); i += 1; continue
        indent = m.group(1)
        end_re = re.compile(rf"^{re.escape(indent)}end\b")
        j = i + 1
        while j < n and not end_re.match(lines[j]):
            j += 1
        if j >= n or j - i - 1 < 2:
            out.append(lines[i]); i += 1; continue
        body_n = j - i - 1
        out.append(lines[i])
        out.append(f"{indent}  # … {body_n} lines")
        out.append(lines[j])
        i = j + 1
    return "\n".join(out)


# ---------------------------------------------------------------- dispatch --
def strip_comments(text: str, lang: str) -> str:
    """Comments and docstrings."""
    l = LANGS.get(lang)
    if not l:
        return text
    if l.comments == "python":
        return py_strip_comments(py_strip_docstrings(text))
    if l.comments in _STYLE:
        return strip_comments_generic(text, l.comments)
    return text


def strip_comments_only(text: str, lang: str) -> str:
    """Comments but not docstrings (skeleton keeps the first docstring line)."""
    l = LANGS.get(lang)
    if not l:
        return text
    if l.comments == "python":
        return py_strip_comments(text)
    if l.comments in _STYLE:
        return strip_comments_generic(text, l.comments)
    return text


def skeleton(text: str, lang: str) -> str:
    l = LANGS.get(lang)
    if not l:
        return text
    if l.skeleton == "python":
        return py_skeleton(text)
    if l.skeleton == "brace":
        return brace_skeleton(text, l.comments if l.comments in _STYLE else "c")
    if l.skeleton == "ruby":
        return ruby_skeleton(text)
    return text


# backwards-compatible names used in tests
js_strip_comments = lambda t: strip_comments_generic(t, "c")  # noqa: E731
js_skeleton = lambda t: brace_skeleton(t, "c")  # noqa: E731
