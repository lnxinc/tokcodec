"""Source-code codec.

Level 2: strip comments and docstrings (the model can usually infer intent from
names; keep them when you need the *why*).
Level 3: skeleton - keep imports, signatures, class layout, first docstring
line; drop function bodies. This is the "I-frame": enough to navigate and
decide what to read in full.
"""
from __future__ import annotations

import ast
import io
import re
import tokenize


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
                if keep_doc:
                    doc = first.value.value.strip().split("\n")[0]
                    doc_line = f'{indent}"""{doc}"""'
                    cuts.append((start, end, f"{doc_line}\n{indent}...  # {n} line{'s' if n != 1 else ''}"))
                else:
                    cuts.append((start, end, f"{indent}...  # {n} line{'s' if n != 1 else ''}"))
            elif isinstance(node, ast.ClassDef):
                visit(node)

    visit(tree)
    for start, end, repl in sorted(cuts, reverse=True):
        lines[start:end] = [repl]
    return "\n".join(lines)


# ------------------------------------------------------------------- JS ----
def _scan(text: str, start: int):
    """Yield (index, char, in_code) walking from start, tracking strings/comments."""
    i, n = start, len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j < 0 else j
            for k in range(i, j):
                yield k, text[k], False
            i = j
            continue
        if c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                yield k, text[k], False
            i = j
            continue
        if c in "'\"`":
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


def js_strip_comments(text: str) -> str:
    keep = []
    i, n = 0, len(text)
    while i < n:
        c, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i); i = n if j < 0 else j; continue
        if c == "/" and nxt == "*":
            j = text.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        if c in "'\"`":
            q, j = c, i + 1
            while j < n and text[j] != q:
                j += 2 if text[j] == "\\" else 1
            keep.append(text[i:j + 1]); i = j + 1; continue
        keep.append(c); i += 1
    return "".join(keep)


def _matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    for i, ch, in_code in _scan(text, open_idx):
        if not in_code:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


JS_FUNC = re.compile(
    r"^[ \t]*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\b[^{]*\{"
    r"|^[ \t]*(?:export\s+)?(?:const|let|var)\s+\w+\s*(?::[^=]+)?=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::[^=]+)?=>\s*\{"
    r"|^[ \t]*(?:public\s+|private\s+|protected\s+|static\s+|async\s+|get\s+|set\s+|override\s+)*#?\w+\s*(?:<[^>]*>)?\([^)]*\)\s*(?::\s*[^{]+)?\{[ \t]*$",
    re.M,
)


def js_skeleton(text: str) -> str:
    pos = 0
    out = []
    while True:
        m = JS_FUNC.search(text, pos)
        if not m:
            out.append(text[pos:])
            break
        open_idx = text.index("{", m.start())
        close_idx = _matching_brace(text, open_idx)
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


# ---------------------------------------------------------------- dispatch --
def strip_comments(text: str, lang: str) -> str:
    if lang == "python":
        return py_strip_comments(py_strip_docstrings(text))
    if lang == "js":
        return js_strip_comments(text)
    return text


def strip_comments_only(text: str, lang: str) -> str:
    """Comments but not docstrings (skeleton keeps the first docstring line)."""
    if lang == "python":
        return py_strip_comments(text)
    if lang == "js":
        return js_strip_comments(text)
    return text


def skeleton(text: str, lang: str) -> str:
    if lang == "python":
        return py_skeleton(text)
    if lang == "js":
        return js_skeleton(text)
    return text
