"""`tokcodec serve` - an MCP server (stdio) exposing tokcodec to any MCP client.

Tools:
  read_compact(path, level=3, kind="auto")   read a file through tokcodec
  compact_text(text, kind="auto", level=2)   compress text you already have
  token_count(text)                          proxy token count

Install the extra:  uv tool install "tokcodec[mcp]"   (or pipx install "tokcodec[mcp]")
Claude Code:        claude mcp add tokcodec -- tokcodec serve
"""
from __future__ import annotations

from pathlib import Path

from .count import count_tokens
from .langs import KINDS
from .pipeline import encode


def _check_kind(kind: str) -> None:
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r}; one of {', '.join(KINDS)}")


def read_compact(path: str, level: int = 3, kind: str = "auto") -> str:
    """Read a file through tokcodec. level 1 = lossless, 2 = comments/timestamps out,
    3 = outline (function bodies collapsed, logs truncated to errors). The result
    begins with a one-line header giving kind and before/after token counts."""
    _check_kind(kind)
    p = Path(path).expanduser()
    raw = p.read_text(encoding="utf-8", errors="replace")
    r = encode(raw, level=level, kind=kind, path=str(p))
    return f"[tokcodec {p} kind={r.kind} level={r.level} {r.tokens_before}→{r.tokens_after} tokens]\n{r.encoded}"


def compact_text(text: str, kind: str = "auto", level: int = 2) -> str:
    """Compress text (a log, JSON, or source) the same way read_compact does."""
    _check_kind(kind)
    r = encode(text, level=level, kind=kind)
    return f"[tokcodec kind={r.kind} level={r.level} {r.tokens_before}→{r.tokens_after} tokens]\n{r.encoded}"


def token_count(text: str) -> int:
    """Approximate token count (tiktoken o200k_base proxy)."""
    return count_tokens(text)


def build_server():
    try:  # mcp >= 2
        from mcp.server import MCPServer as Server
    except ImportError:
        try:  # mcp 1.x
            from mcp.server.fastmcp import FastMCP as Server
        except ImportError as e:
            raise SystemExit(
                "tokcodec serve needs the `mcp` package. Install with:\n"
                "  uv tool install 'tokcodec[mcp]'   or   pipx install 'tokcodec[mcp]'"
            ) from e
    mcp = Server("tokcodec")
    mcp.tool()(read_compact)
    mcp.tool()(compact_text)
    mcp.tool()(token_count)
    return mcp


def main() -> int:
    build_server().run()  # stdio
    return 0
