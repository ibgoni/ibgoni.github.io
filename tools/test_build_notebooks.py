#!/usr/bin/env python3
"""Tests for the notebook publishing pipeline.

    python3 tools/test_build_notebooks.py

No test framework needed — it prints a line per case and exits non-zero on the
first failure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_notebooks as bn  # noqa: E402

FAILURES = []


def check(name, got, want):
    ok = got == want
    print(("  ok   " if ok else "  FAIL ") + name)
    if not ok:
        print(f"         got  {got!r}")
        print(f"         want {want!r}")
        FAILURES.append(name)


print("parse_front_matter")

check(
    "simple key/value",
    bn.parse_front_matter("---\ntitle: Hello\n---\n"),
    {"title": "Hello"},
)

# The bug this suite exists for: a summary folded over several lines used to be
# truncated at the first line.
check(
    "folded multi-line value",
    bn.parse_front_matter(
        "---\n"
        "title: A\n"
        "summary: first line\n"
        "  second line\n"
        "  third line\n"
        "---\n"
    ),
    {"title": "A", "summary": "first line second line third line"},
)

check(
    "a colon inside a folded line does not start a key",
    bn.parse_front_matter("---\nsummary: one\n  two: still the summary\n---\n"),
    {"summary": "one two: still the summary"},
)

check(
    "inline list",
    bn.parse_front_matter("---\ntags: [a, b, c]\n---\n"),
    {"tags": ["a", "b", "c"]},
)

check(
    "block list",
    bn.parse_front_matter("---\ntags:\n  - a\n  - b\n---\n"),
    {"tags": ["a", "b"]},
)

check(
    "booleans",
    bn.parse_front_matter("---\ndraft: true\npublic: no\n---\n"),
    {"draft": True, "public": False},
)

check("no front matter returns None", bn.parse_front_matter("# Just a heading"), None)

check(
    "comments and blank lines are ignored",
    bn.parse_front_matter("---\n# a comment\n\ntitle: T\n---\n"),
    {"title": "T"},
)

print("\nhtml cleaning")

check(
    "pandas <style scoped> blocks are dropped",
    bn.clean_body('<div><style scoped="">.dataframe td { color: red }</style><p>x</p></div>'),
    "<div><p>x</p></div>",
)

check(
    "a cell emptied by hide-input is removed",
    bn.clean_body('<div class="cell code_cell celltag_hide-input" id="cell-id=abc">\n</div>'),
    "",
)

check(
    "cell ids lose the equals sign",
    bn.clean_body('<div class="cell" id="cell-id=ab12">x</div>'),
    '<div class="cell" id="cell-ab12">x</div>',
)

print("\ntable of contents")

check(
    "headings become entries without the pilcrow",
    bn.build_toc(
        '<h2 id="one">One<a class="anchor-link" href="#one">¶</a></h2>'
        '<h3 id="two">Two<a class="anchor-link" href="#two">¶</a></h3>'
        '<h4 id="skip">Not collected</h4>'
    ),
    [{"level": 2, "id": "one", "text": "One"},
     {"level": 3, "id": "two", "text": "Two"}],
)

print("\nescaping")

check(
    "titles with quotes cannot break an attribute",
    bn.esc('He said "no" & left'),
    "He said &quot;no&quot; &amp; left",
)

print()
if FAILURES:
    print(f"{len(FAILURES)} failure(s): {', '.join(FAILURES)}")
    raise SystemExit(1)
print("all passed")
