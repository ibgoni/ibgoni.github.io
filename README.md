# Academic Website — Ibrahim Goni Abdoulkadiri

Personal academic website of Ibrahim Goni Abdoulkadiri, Ph.D. candidate in
development economics at CERDI (Université Clermont Auvergne, CNRS, IRD).

Live site: https://ibgoni.github.io/

## Structure

- `index.html` — home page (bio, photo, contact)
- `research.html` — working papers and work in progress, with expandable abstracts
- `teaching.html` — teaching hub, generated from `_data/teaching.yml`
- `teaching/<course>/` — course pages; `teaching/<course>/<session>/` — session pages
- `assets/cv/Ibrahim_Goni_CV.pdf` — downloadable CV
- `assets/css/style.css` — shared stylesheet
- `assets/img/portrait.jpg` — profile photo

Deployed with GitHub Pages, which builds the site with Jekyll: every
change merged into `main` is live about a minute later (allow up to
10 minutes for the HTTP cache). `index.html` and `research.html` are plain
HTML; the teaching pages use the layouts in `_layouts/` and `_includes/`.

## How to update

- **Text or a new paper**: edit the relevant HTML file (e.g.
  `research.html`) directly on GitHub (pencil icon). To add a paper,
  copy an existing `<article class="paper">…</article>` block and edit
  the text inside the tags.
- **CV**: edit `assets/cv/cv-source.html`, open it in Chrome, print to
  PDF (A4, default margins, no browser headers/footers) and replace
  `assets/cv/Ibrahim_Goni_CV.pdf`. Full instructions are in a comment
  at the top of the source file.
- **Photo**: replace `assets/img/portrait.jpg` (keep the same filename).

## Teaching materials

Everything about courses and sessions (titles, guiding question,
overview, objectives, session plan, exercises, readings with DOI and
replication links, one-line notes on each data file, links to authors'
replication data that are not hosted here) lives in `_data/teaching.yml`;
the field list is at the top of that file. Files are listed on the session
page automatically:

```
teaching/econometrics/s01/
├── index.html          # 5-line stub: layout: session, course: econometrics, session: s01
├── worksheet/          # student worksheet (PDF)
├── slides/
├── code/               # do-files, R scripts
├── data/               # replication data
├── readings/           # open-access papers only; link others by DOI in teaching.yml
└── Goni-Abdoulkadiri_econometrics_s01.zip   # one-click package (built, see below)
```

To add a session: create the folder and its `index.html` stub (copy one
from another session and change `session:`), drop the files into the
subfolders, and add the session's entry under the course in
`_data/teaching.yml`.

Never upload solutions, teacher notes, LaTeX sources (they contain the
solutions), solution do-files or student lists: the folders are public.

Before publishing a worksheet, stamp it so every page carries the author,
licence and source URL in its footer and metadata, then rebuild the
session packages (README with citation, licence and sources included):

```
pip install pypdf reportlab pyyaml
python _tools/stamp_pdfs.py --title "Econometrics, Session 1: worksheet" teaching/econometrics/s01/worksheet/*.pdf
python _tools/build_packages.py
```

Worksheets are released under CC BY-NC-ND 4.0. Only host files written by
Ibrahim, plus small teaching datasets with their source stated; authors'
replication files are linked to their official archive (`external_data`).
Documents by others (e.g. the SED syllabus) are not hosted: the course page
credits their authors.
