#!/usr/bin/env python3
"""Publish Jupyter notebooks as pages of the website.

Every ``notebooks/*.ipynb`` becomes ``notebooks/<name>.html``, styled like the
rest of the site, and all of them are listed on ``notebooks.html``.

    python3 tools/build_notebooks.py              # convert (uses saved outputs)
    python3 tools/build_notebooks.py --execute    # re-run the notebooks first
    python3 tools/build_notebooks.py --check      # fail if the HTML is stale

Notebooks carry their own metadata in a front-matter cell: make the *first*
cell of the notebook a raw (or markdown) cell containing

    ---
    title: Event study with staggered adoption
    date: 2026-07-20
    summary: One or two sentences, shown on the notebooks index.
    tags: [difference-in-differences, python]
    draft: false
    ---

Everything is optional. Without a title we fall back to the first ``# heading``
of the notebook, and without a date to the file's last commit.

Cell tags control what the reader sees:

    hide-input     hide the code, keep the output
    hide-output    keep the code, hide the output
    remove-cell    drop the cell entirely
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import nbformat
    from nbconvert import HTMLExporter
    from traitlets.config import Config
except ImportError:  # pragma: no cover - dependency hint
    sys.exit(
        "Missing dependencies. Install them with:\n"
        "    pip install nbformat nbconvert\n"
        "(add nbclient ipykernel if you want --execute)"
    )

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_DIR = ROOT / "notebooks"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
INDEX_PAGE = ROOT / "notebooks.html"

SITE_URL = "https://ibgoni.github.io"
REPO_URL = "https://github.com/ibgoni/ibgoni.github.io"

# Tags understood by the TagRemovePreprocessor.
HIDE_INPUT_TAG = "hide-input"
HIDE_OUTPUT_TAG = "hide-output"
REMOVE_CELL_TAG = "remove-cell"


# --------------------------------------------------------------------------- #
# Front matter
# --------------------------------------------------------------------------- #

FRONT_MATTER_RE = re.compile(r"\A\s*---\s*\n(.*?)\n\s*---\s*\n?\Z", re.DOTALL)


def _parse_scalar(raw: str):
    """Turn a front-matter value into a str, bool, or list of str."""
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("\"'") for item in inner.split(",") if item.strip()]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    lowered = value.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    return value


def parse_front_matter(text: str) -> dict | None:
    """Parse a ``---`` delimited block. Returns None when there is none.

    Supports the two YAML shapes people actually type in a front-matter cell:
    ``key: value``, and a value folded over several indented lines. An indented
    line always continues the key above it, so a colon inside a sentence does
    not start a new key.
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return None
    meta: dict = {}
    key = None
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line[:1] in (" ", "\t") and key is not None:
            if stripped.startswith("- "):
                if not isinstance(meta.get(key), list):
                    meta[key] = []
                meta[key].append(stripped[2:].strip().strip("\"'"))
            elif isinstance(meta.get(key), str) and meta[key]:
                meta[key] = meta[key] + " " + stripped      # folded scalar
            elif not meta.get(key):
                meta[key] = stripped
            continue

        if ":" not in line:
            continue
        key, _, raw = line.partition(":")
        key = key.strip()
        meta[key] = _parse_scalar(raw) if raw.strip() else ""
    return meta


# --------------------------------------------------------------------------- #
# Notebook model
# --------------------------------------------------------------------------- #


@dataclass
class Notebook:
    source: Path
    slug: str
    title: str
    date: dt.date
    summary: str
    tags: list = field(default_factory=list)
    draft: bool = False
    body: str = ""
    toc: list = field(default_factory=list)
    needs_math: bool = False
    has_outputs: bool = True

    @property
    def output(self) -> Path:
        return NOTEBOOK_DIR / f"{self.slug}.html"

    @property
    def url(self) -> str:
        return f"/notebooks/{self.slug}.html"

    @property
    def date_label(self) -> str:
        return self.date.strftime("%d %B %Y").lstrip("0")

    @property
    def date_iso(self) -> str:
        return self.date.isoformat()


def git_date(path: Path) -> dt.date | None:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        ).stdout.strip()
        if out:
            return dt.date.fromisoformat(out)
    except Exception:
        pass
    return None


def take_front_matter(nb) -> dict:
    """Pull metadata off the notebook, removing the front-matter cell."""
    meta = dict(nb.metadata.get("site", {}))
    if nb.cells:
        first = nb.cells[0]
        if first.cell_type in ("raw", "markdown"):
            parsed = parse_front_matter(first.source)
            if parsed is not None:
                meta.update(parsed)
                nb.cells.pop(0)
    return meta


def take_title(nb) -> str | None:
    """Use the first markdown H1 as the title and drop it from the body.

    The page template prints the title in the header, so leaving it in the
    notebook body would show it twice.
    """
    for index, cell in enumerate(nb.cells):
        if cell.cell_type != "markdown":
            continue
        lines = cell.source.splitlines()
        for line_no, line in enumerate(lines):
            if not line.strip():
                continue
            if line.startswith("# "):
                title = line[2:].strip()
                remainder = "\n".join(lines[:line_no] + lines[line_no + 1 :]).strip()
                if remainder:
                    nb.cells[index].source = remainder
                else:
                    nb.cells.pop(index)
                return title
            break  # first non-blank line is not an H1
        break  # only inspect the first markdown cell
    return None


MATH_RE = re.compile(r"\$\$?[^$]|\\\(|\\\[|\\begin\{(?:equation|align|aligned|cases|pmatrix|bmatrix)")


def detect_math(nb) -> bool:
    return any(
        cell.cell_type == "markdown" and MATH_RE.search(cell.source)
        for cell in nb.cells
    )


def has_stored_outputs(nb) -> bool:
    return any(
        cell.cell_type == "code" and cell.get("outputs")
        for cell in nb.cells
    )


# --------------------------------------------------------------------------- #
# HTML post-processing
# --------------------------------------------------------------------------- #

# pandas emits <style scoped> blocks; `scoped` was removed from the HTML spec,
# so those rules would leak into the whole page. We style .dataframe ourselves.
DATAFRAME_STYLE_RE = re.compile(
    r"<style[^>]*>(?:(?!</style>).)*?\.dataframe(?:(?!</style>).)*?</style>",
    re.DOTALL | re.IGNORECASE,
)
HEADING_RE = re.compile(r'<h([23])\s+id="([^"]+)">(.*?)</h\1>', re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
EMPTY_CELL_RE = re.compile(r'<div class="cell[^"]*"[^>]*>\s*</div>')


def clean_body(body: str) -> str:
    body = DATAFRAME_STYLE_RE.sub("", body)
    body = EMPTY_CELL_RE.sub("", body)
    # nbconvert emits ids like `cell-id=9cebdd76`; `=` is legal in an id but
    # makes the fragment awkward to link to.
    body = re.sub(r'id="cell-id=([0-9a-f]+)"', r'id="cell-\1"', body)
    return body.strip()


def build_toc(body: str) -> list:
    toc = []
    for level, anchor, inner in HEADING_RE.findall(body):
        text = TAG_RE.sub("", inner).replace("¶", "").strip()
        if text:
            toc.append({"level": int(level), "id": anchor, "text": text})
    return toc


def convert(nb) -> str:
    config = Config()
    config.TagRemovePreprocessor.enabled = True
    config.TagRemovePreprocessor.remove_cell_tags = (REMOVE_CELL_TAG,)
    config.TagRemovePreprocessor.remove_input_tags = (HIDE_INPUT_TAG,)
    config.TagRemovePreprocessor.remove_all_outputs_tags = (HIDE_OUTPUT_TAG,)
    config.HTMLExporter.preprocessors = [
        "nbconvert.preprocessors.TagRemovePreprocessor"
    ]
    # `basic` emits the notebook body with no styling of its own, which is what
    # we want: assets/css/notebook.css dresses it in the site's colours.
    exporter = HTMLExporter(config=config, template_name="basic")
    exporter.exclude_input_prompt = True
    exporter.exclude_output_prompt = True
    body, _ = exporter.from_notebook_node(nb)
    return clean_body(body)


def execute(nb, path: Path) -> None:
    try:
        from nbclient import NotebookClient
    except ImportError:
        sys.exit("--execute needs nbclient: pip install nbclient ipykernel")
    kernel = nb.metadata.get("kernelspec", {}).get("name", "python3")
    print(f"  running ({kernel}) ...", flush=True)
    NotebookClient(
        nb,
        timeout=900,
        kernel_name=kernel,
        allow_errors=False,
        resources={"metadata": {"path": str(path.parent)}},
    ).execute()


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def render(template: str, values: dict) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def render_toc(toc: list) -> str:
    if len(toc) < 3:
        return ""
    items = "\n".join(
        f'        <li class="toc-l{entry["level"]}">'
        f'<a href="#{esc(entry["id"])}">{esc(entry["text"])}</a></li>'
        for entry in toc
    )
    return (
        '      <nav class="nb-toc" aria-label="On this page">\n'
        '        <p class="toc-label">On this page</p>\n'
        "        <ul>\n" + items + "\n        </ul>\n"
        "      </nav>"
    )


def render_tags(tags: list) -> str:
    if not tags:
        return ""
    chips = "".join(f'<span class="chip">{esc(str(t))}</span>' for t in tags)
    return f'<p class="nb-tags">{chips}</p>'


MATHJAX = """  <script>
    window.MathJax = {
      tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']] },
      options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] }
    };
  </script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>"""


def build_page(notebook: Notebook, template: str) -> str:
    return render(
        template,
        {
            "TITLE": esc(notebook.title),
            "SUMMARY": esc(notebook.summary),
            "SUMMARY_BLOCK": (
                f'<p class="nb-summary">{esc(notebook.summary)}</p>'
                if notebook.summary
                else ""
            ),
            "SLUG": notebook.slug,
            "URL": notebook.url,
            "CANONICAL": SITE_URL + notebook.url,
            "DATE_ISO": notebook.date_iso,
            "DATE_LABEL": notebook.date_label,
            "TAGS": render_tags(notebook.tags),
            "TOC": render_toc(notebook.toc),
            "BODY": notebook.body,
            "SOURCE_URL": f"{REPO_URL}/blob/main/notebooks/{notebook.source.name}",
            "DOWNLOAD_URL": f"/notebooks/{notebook.source.name}",
            "MATHJAX": MATHJAX if notebook.needs_math else "",
            "YEAR": str(dt.date.today().year),
            "UPDATED": dt.date.today().strftime("%B %Y"),
        },
    )


def build_index(notebooks: list, template: str) -> str:
    if notebooks:
        cards = "\n".join(
            f"""    <article class="nb-card">
      <p class="nb-card-date"><time datetime="{n.date_iso}">{n.date_label}</time></p>
      <h3><a href="{n.url}">{esc(n.title)}</a></h3>
      {f'<p class="nb-card-summary">{esc(n.summary)}</p>' if n.summary else ''}
      {render_tags(n.tags)}
    </article>"""
            for n in notebooks
        )
        listing = f'  <div class="nb-grid">\n{cards}\n  </div>'
    else:
        listing = (
            '  <p class="empty-note">No notebook published yet. Drop an '
            "<code>.ipynb</code> file into <code>notebooks/</code> and it will "
            "appear here.</p>"
        )
    return render(
        template,
        {
            "LISTING": listing,
            "COUNT": str(len(notebooks)),
            "YEAR": str(dt.date.today().year),
            "UPDATED": dt.date.today().strftime("%B %Y"),
        },
    )


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #


def load(path: Path, run: bool) -> Notebook | None:
    nb = nbformat.read(path, as_version=4)
    meta = take_front_matter(nb)

    if meta.get("draft"):
        print(f"  skipped (draft): {path.name}")
        return None

    if run:
        execute(nb, path)

    heading_title = take_title(nb)
    title = str(meta.get("title") or heading_title or path.stem.replace("-", " ").title())

    raw_date = meta.get("date")
    date = None
    if raw_date:
        try:
            date = dt.date.fromisoformat(str(raw_date)[:10])
        except ValueError:
            print(f"  warning: unreadable date {raw_date!r} in {path.name}")
    if date is None:
        date = git_date(path) or dt.date.fromtimestamp(path.stat().st_mtime)

    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    stored = has_stored_outputs(nb)
    needs_math = detect_math(nb)
    body = convert(nb)

    return Notebook(
        source=path,
        slug=path.stem,
        title=title,
        date=date,
        summary=str(meta.get("summary") or ""),
        tags=list(tags),
        draft=False,
        body=body,
        toc=build_toc(body),
        needs_math=needs_math,
        has_outputs=stored,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--execute",
        action="store_true",
        help="run each notebook before converting (needs nbclient and a kernel)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if any generated file is out of date",
    )
    args = parser.parse_args()

    page_template = (TEMPLATE_DIR / "notebook.html").read_text(encoding="utf-8")
    index_template = (TEMPLATE_DIR / "notebooks-index.html").read_text(encoding="utf-8")

    NOTEBOOK_DIR.mkdir(exist_ok=True)
    sources = sorted(p for p in NOTEBOOK_DIR.glob("*.ipynb") if not p.name.startswith("."))

    if not sources:
        print("No notebook found in notebooks/.")

    notebooks: list = []
    for path in sources:
        print(f"- {path.name}")
        notebook = load(path, args.execute)
        if notebook is None:
            continue
        if not notebook.has_outputs:
            print(
                "  warning: no saved output — run the notebook and save it, "
                "or build with --execute"
            )
        notebooks.append(notebook)

    notebooks.sort(key=lambda n: (n.date, n.title), reverse=True)

    written: list = []
    stale: list = []

    def emit(path: Path, content: str) -> None:
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == content:
            return
        if args.check:
            stale.append(path)
            return
        path.write_text(content, encoding="utf-8")
        written.append(path)

    for notebook in notebooks:
        emit(notebook.output, build_page(notebook, page_template))
    emit(INDEX_PAGE, build_index(notebooks, index_template))

    # Remove pages whose notebook is gone or has become a draft.
    keep = {n.output.name for n in notebooks}
    for orphan in NOTEBOOK_DIR.glob("*.html"):
        if orphan.name not in keep:
            if args.check:
                stale.append(orphan)
            else:
                orphan.unlink()
                print(f"  removed stale page {orphan.name}")

    if args.check:
        if stale:
            print("\nOut of date:")
            for path in stale:
                print(f"  {path.relative_to(ROOT)}")
            print("Run: python3 tools/build_notebooks.py")
            return 1
        print("\nUp to date.")
        return 0

    print(
        f"\n{len(notebooks)} notebook(s) published, "
        f"{len(written)} file(s) written."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
