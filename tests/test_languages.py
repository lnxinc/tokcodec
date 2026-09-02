"""Every supported language: comments go, signatures stay, bodies collapse."""
import pytest

from tokcodec import encode
from tokcodec.detect import detect
from tokcodec.transforms import code

GO = '''package main

import "fmt"

// Server holds state.
type Server struct {
    addr string // listen address
}

// Start runs the server.
func (s *Server) Start(ctx context.Context) error {
    if s.addr == "" {
        return fmt.Errorf("no addr: %s", "{")
    }
    return nil
}

func helper(a, b int) int {
    return a + b
}
'''

RUST = '''use std::fmt;

/// A point.
pub struct Point { x: i32, y: i32 }

impl Point {
    /// Make one.
    pub fn new(x: i32, y: i32) -> Self {
        let s = "}"; // tricky
        Point { x, y }
    }

    pub async fn dist(&self) -> f64 {
        match self.x {
            0 => 0.0,
            _ => ((self.x * self.x + self.y * self.y) as f64).sqrt(),
        }
    }
}
'''

JAVA = '''package demo;

import java.util.List;

/** Doc. */
public class Greeter<T> {
    private final String name; // field

    public Greeter(String name) {
        this.name = name;
        validate();
    }

    @Override
    public <R> List<R> greet(List<T> items, int n) throws Exception {
        if (n > 0) {
            return null;
        }
        return List.of();
    }
}
'''

CSHARP = '''namespace Demo
{
    public class Calc
    {
        // Allman style
        public int Add(int a, int b)
        {
            var s = "}";
            return a + b;
        }

        public static async Task<int> RunAsync(string path)
        {
            using (var f = File.OpenRead(path))
            {
                return await Task.FromResult(1);
            }
        }
    }
}
'''

KOTLIN = '''package demo

data class User(val name: String, val age: Int) {
    fun isAdult(): Boolean {
        val s = "}"
        return age >= 18
    }
}

fun <T> List<T>.second(): T? {
    if (size < 2) return null
    return this[1]
}
'''

C = '''#include <stdio.h>

/* A struct. */
struct node { int v; struct node *next; };

static int add(int a, int b) {
    // add
    return a + b;
}

int main(int argc, char **argv)
{
    printf("%s\\n", "{");
    for (int i = 0; i < argc; i++) {
        add(i, 1);
    }
    return 0;
}
'''

RUBY = '''# frozen_string_literal: true
require "set"

module Demo
  class Greeter
    attr_reader :name # the name

    def initialize(name)
      @name = name
      @greeting = "hi # not a comment"
    end

    def greet(other = nil)
      if other
        "#{@greeting} #{other}"
      else
        @greeting
      end
    end

    def short; 1; end
  end
end
'''


@pytest.mark.parametrize(
    "lang,src,keep,drop",
    [
        ("go", GO, ["func (s *Server) Start(ctx context.Context) error {", "func helper(a, b int) int {", "type Server struct {", "addr string"],
         ["listen address", "no addr", "return a + b"]),
        ("rust", RUST, ["pub fn new(x: i32, y: i32) -> Self {", "pub async fn dist(&self) -> f64 {", "impl Point {", "pub struct Point"],
         ["tricky", "sqrt()", "let s ="]),
        ("java", JAVA, ["public Greeter(String name) {", "public <R> List<R> greet(List<T> items, int n) throws Exception {", "public class Greeter<T> {", "@Override"],
         ["/** Doc. */", "validate();", "return List.of();"]),
        ("csharp", CSHARP, ["public int Add(int a, int b)", "public static async Task<int> RunAsync(string path)", "public class Calc"],
         ["Allman style", "return a + b;", "File.OpenRead"]),
        ("kotlin", KOTLIN, ["fun isAdult(): Boolean {", "fun <T> List<T>.second(): T? {", "data class User(val name: String, val age: Int) {"],
         ["return age >= 18", "return this[1]"]),
        ("c", C, ["static int add(int a, int b) {", "int main(int argc, char **argv)", "struct node { int v; struct node *next; };", "#include <stdio.h>"],
         ["/* A struct. */", "// add", "printf(", "for (int i"]),
        ("ruby", RUBY, ["def initialize(name)", "def greet(other = nil)", "class Greeter", "module Demo", "def short; 1; end", "attr_reader :name"],
         ["frozen_string_literal", "the name", "@name = name", "#{@greeting}"]),
    ],
)
def test_level3_outline(lang, src, keep, drop):
    out = encode(src, level=3, kind=lang, count=False).encoded
    for k in keep:
        assert k.strip() in out.replace("\n ", "\n"), (lang, k, out)
    for d in drop:
        assert d not in out, (lang, d, out)
    assert "lines" in out  # a marker was left


def test_level2_keeps_bodies_drops_comments():
    out = encode(GO, level=2, kind="go", count=False).encoded
    assert "return a + b" in out and "listen address" not in out
    assert 'fmt.Errorf("no addr: %s", "{")' in out  # string with brace intact


def test_hash_comments_string_aware():
    src = 'echo "a # not comment" # real\nX=1 # trailing\n# full line\nURL="http://x/#anchor"\n'
    out = code.strip_comments(src, "shell")
    assert 'echo "a # not comment"' in out and "real" not in out
    assert "X=1" in out and "trailing" not in out and "full line" not in out
    assert '"http://x/#anchor"' in out


def test_sql_and_markup_comments():
    assert "--" not in code.strip_comments("SELECT 1; -- c\n/* b */ SELECT '--' AS x;", "sql").replace("'--'", "")
    assert "<!--" not in code.strip_comments("<a><!-- gone --><b>keep</b></a>", "markup")


def test_control_flow_is_never_collapsed():
    src = "if (x) {\n  a();\n  b();\n}\nwhile (y) {\n  c();\n  d();\n}\n"
    assert code.brace_skeleton(src) == src


def test_detect_by_extension_and_sniff():
    assert detect("", "main.go") == "go"
    assert detect("", "lib.rs") == "rust"
    assert detect("", "App.kt") == "kotlin"
    assert detect("", "Dockerfile") == "shell"
    assert detect("", "Gemfile") == "ruby"
    assert detect(GO) == "go"
    assert detect(RUST) == "rust"
    assert detect(JAVA) == "java"
    assert detect("<!DOCTYPE html><html></html>") == "markup"


def test_unknown_kind_errors():
    with pytest.raises(ValueError):
        detect("x", kind="cobol")


PHP = '''<?php
declare(strict_types=1);

namespace App\\Support;

use InvalidArgumentException; // import

# legacy hash comment
/** Doc block. */
#[Attribute(Attribute::TARGET_METHOD)]
final class Money
{
    private int $amount; // cents

    public function __construct(int $amount, private string $currency = "USD")
    {
        $this->amount = $amount; # trailing
        $tag = "#not-a-comment {";
    }

    public static function of(int|float $amount, string $currency): static
    {
        if ($amount < 0) {
            throw new InvalidArgumentException("negative");
        }
        return new static((int) round($amount * 100), $currency);
    }

    public function format(): string { return sprintf("%s %.2f", $this->currency, $this->amount / 100); }
}
'''


def test_php_outline_and_comments():
    out = encode(PHP, level=3, kind="php", count=False).encoded
    for keep in ["<?php", "namespace App\\Support;", "#[Attribute(Attribute::TARGET_METHOD)]", "final class Money",
                 "public function __construct(int $amount, private string $currency = \"USD\")",
                 "public static function of(int|float $amount, string $currency): static",
                 "public function format(): string { return sprintf(", "private int $amount;"]:
        assert keep in out, (keep, out)
    for drop in ["// import", "legacy hash", "Doc block", "$this->amount = $amount", "throw new", "trailing"]:
        assert drop not in out, (drop, out)
    l2 = encode(PHP, level=2, kind="php", count=False).encoded
    assert '$tag = "#not-a-comment {";' in l2 and "# trailing" not in l2


def test_php_detect():
    assert detect("", "index.php") == "php"
    assert detect(PHP) == "php"
