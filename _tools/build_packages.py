"""Build the one-click package (.zip) of every published teaching session.

For each session listed in _data/teaching.yml, the files found in
teaching/<course>/<session>/{worksheet,slides,code,data,readings}/ are
zipped together with a README.txt (author, licence, citation, sources) into
teaching/<course>/<session>/Goni-Abdoulkadiri_<course>_<session>.zip.
Archives are reproducible: rebuilding unchanged sessions gives identical files.

Run from the repository root, after stamping the PDFs:
    python _tools/build_packages.py

Requires: pip install pyyaml
"""

import textwrap
import zipfile
from datetime import date
from pathlib import Path

import yaml

ROOT = Path.cwd()
SITE = "https://ibgoni.github.io"
GROUPS = ["worksheet", "slides", "code", "data", "readings"]
PREFIX = "Goni-Abdoulkadiri"


def wrap(text, indent="  "):
    return textwrap.fill(" ".join(str(text).split()), width=76,
                         initial_indent=indent, subsequent_indent=indent,
                         break_on_hyphens=False, break_long_words=False)


def readme(T, c, s, files):
    url = f"{SITE}{c['url']}{s['id']}/"
    year = str(s.get("published", "2026"))[:4]
    lines = [
        f"{c['title']} - Session {s['number']}: {s['title']}",
    ]
    if c.get("title_local") or s.get("title_local"):
        lines.append(f"{c.get('title_local', c['title'])} - Séance {s['number']} : {s.get('title_local', s['title'])}")
    lines += [
        f"{c['programme']}, {c['institution']}, {c['year']}",
        "",
        f"Author:  {T['author']}",
        f"Source:  {url}",
        "",
        "CONTENTS",
    ]
    notes = s.get("notes") or {}
    for rel in files:
        lines.append(f"  {rel}")
        name = Path(rel).name
        if name in notes:
            lines.append(wrap(notes[name], indent="      "))
    ext = s.get("external_data") or []
    if ext:
        lines += ["", "AUTHORS' REPLICATION DATA (not included, download from the source)"]
        for x in ext:
            lines.append(f"  {x['name']}  <{x['url']}>")
            lines.append(wrap(f"{x['source']}. {x['note']}", indent="      "))
    apps = s.get("applications") or []
    if apps:
        lines += ["", "READINGS"]
        for a in apps:
            ref = " ".join(str(a.get("ref", a.get("cite", ""))).split())
            if a.get("url"):
                ref += f" {a['url']}"
            lines.append(wrap(f"[{a.get('role', 'Reading')}] {ref}"))
    lines += [
        "",
        "HOW TO CITE",
        wrap(f"{T['author_cite']} ({year}). Session {s['number']}: {s['title']}. "
             f"{c['title']}, {c['programme']}, {c['institution']}. {url}"),
        "",
        "LICENCE",
        wrap(f"Worksheet (c) {year} {T['author']}, released under {T['license']['long']} "
             f"({T['license']['url']}): you may share it for non-commercial purposes, "
             f"with attribution and without modification."),
        wrap("Datasets remain the work of their original authors and are subject to "
             "their terms; see READINGS for the source of each application."),
        "",
        "Worksheets are in French. Solutions are discussed in class and are not distributed.",
        "",
    ]
    return "\n".join(lines)


def build(T, c, s):
    folder = ROOT / c["url"].strip("/") / s["id"]
    files = []
    for g in GROUPS:
        d = folder / g
        if d.is_dir():
            files += sorted(p for p in d.iterdir() if p.is_file() and not p.name.startswith("."))
    if not files:
        return None
    stem = f"{PREFIX}_{c['id']}_{s['id']}"
    out = folder / f"{stem}.zip"
    stamp = s.get("published") or date(2026, 1, 1)
    if isinstance(stamp, str):
        stamp = date.fromisoformat(stamp)
    dt = (stamp.year, stamp.month, stamp.day, 12, 0, 0)
    # The worksheet sits at the top of the archive; other files keep their folder.
    rels = [p.name if p.parent.name == "worksheet" else f"{p.parent.name}/{p.name}" for p in files]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        info = zipfile.ZipInfo(f"{stem}/README.txt", dt)
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, readme(T, c, s, rels).encode("utf-8"))
        for p, rel in zip(files, rels):
            info = zipfile.ZipInfo(f"{stem}/{rel}", dt)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return out


if __name__ == "__main__":
    T = yaml.safe_load((ROOT / "_data" / "teaching.yml").read_text(encoding="utf-8"))
    for c in T["courses"]:
        for s in c.get("sessions") or []:
            out = build(T, c, s)
            if out:
                print(f"{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB")
