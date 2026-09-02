"""Language table: how to strip comments and how to outline each language.

comments:  "c"      // and /* */          "hash"  #           "dash"  -- and /* */
           "php"    // # and /* */ (but not #[Attribute])
           "xml"    <!-- -->              "python" (ast + tokenize)   "none"
skeleton:  "python" (ast)   "brace" (scanner + header regex)   "ruby" (def … end)   "none"
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lang:
    name: str
    label: str
    comments: str
    skeleton: str
    exts: tuple[str, ...] = ()
    files: tuple[str, ...] = ()


LANGS: dict[str, Lang] = {}


def _add(*langs: Lang) -> None:
    for l in langs:
        LANGS[l.name] = l


_add(
    Lang("python", "Python", "python", "python", (".py", ".pyi", ".pyw")),
    Lang("js", "JavaScript / TypeScript", "c", "brace", (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".mts", ".cts")),
    Lang("go", "Go", "c", "brace", (".go",)),
    Lang("rust", "Rust", "c", "brace", (".rs",)),
    Lang("java", "Java", "c", "brace", (".java",)),
    Lang("kotlin", "Kotlin", "c", "brace", (".kt", ".kts")),
    Lang("csharp", "C#", "c", "brace", (".cs",)),
    Lang("c", "C / C++ / Objective-C", "c", "brace", (".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".m", ".mm")),
    Lang("swift", "Swift", "c", "brace", (".swift",)),
    Lang("dart", "Dart", "c", "brace", (".dart",)),
    Lang("scala", "Scala", "c", "brace", (".scala", ".sc")),
    Lang("php", "PHP", "php", "brace", (".php", ".phtml", ".inc")),
    Lang("zig", "Zig", "c", "brace", (".zig",)),
    Lang("ruby", "Ruby", "hash", "ruby", (".rb", ".rake", ".gemspec"), ("Gemfile", "Rakefile")),
    Lang("shell", "Shell", "hash", "none", (".sh", ".bash", ".zsh", ".fish", ".ps1"), ("Dockerfile", "Makefile", ".bashrc", ".zshrc")),
    Lang("config", "YAML / TOML / INI", "hash", "none", (".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env", ".properties")),
    Lang("perl", "Perl / R / Elixir", "hash", "none", (".pl", ".pm", ".r", ".R", ".ex", ".exs")),
    Lang("sql", "SQL", "dash", "none", (".sql",)),
    Lang("lua", "Lua / Haskell", "dash", "none", (".lua", ".hs")),
    Lang("css", "CSS / SCSS / Less", "c", "none", (".css", ".scss", ".less")),
    Lang("markup", "HTML / XML / SVG / Vue / Svelte", "xml", "none", (".html", ".htm", ".xml", ".svg", ".vue", ".svelte")),
    # non-code kinds handled by other codecs
    Lang("json", "JSON", "none", "none", (".json", ".jsonl", ".geojson")),
    Lang("log", "Logs / tool output", "none", "none", (".log",)),
    Lang("diff", "Diffs", "none", "none", (".diff", ".patch")),
    Lang("text", "Markdown / prose", "none", "none", (".md", ".rst", ".txt")),
)

EXT_TO_LANG: dict[str, str] = {e: l.name for l in LANGS.values() for e in l.exts}
FILE_TO_LANG: dict[str, str] = {f: l.name for l in LANGS.values() for f in l.files}
KINDS = ["auto", *LANGS]


def is_code(name: str) -> bool:
    l = LANGS.get(name)
    return bool(l) and (l.comments != "none" or l.skeleton != "none")
