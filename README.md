# Academic Website — Ibrahim Goni Abdoulkadiri

Personal academic website of Ibrahim Goni Abdoulkadiri, Ph.D. candidate in
development economics at CERDI (Université Clermont Auvergne, CNRS, IRD).

Live site: https://ibgoni.github.io/

## Structure

- `index.html` — home page (bio, photo, news, contact)
- `research.html` — working papers, work in progress and presentations
- `teaching.html` — teaching hub, generated from `_data/teaching.yml`
- `teaching/<course>/` — course pages; `teaching/<course>/<session>/` — session pages
- `assets/cv/Ibrahim_Goni_CV.pdf` — downloadable CV
- `assets/css/style.css` — shared stylesheet
- `assets/img/portrait.jpg` — profile photo

Deployed with GitHub Pages, which builds the site with Jekyll: every
change merged into `main` is live about a minute later (allow up to
10 minutes for the HTTP cache). Every page shares the layout in
`_layouts/base.html` (head, header with the theme toggle, footer) and the
components in `_includes/`.

## How to update

- **News** (home page): add an item at the top of `_data/news.yml`
  (date, kind, one sentence). The six latest items are shown; older ones
  fold into "Earlier news". Future-dated items get an "Upcoming" badge
  automatically.
- **Presentations**: add an entry to `_data/talks.yml`. It appears on the
  Research page (by year) and, through `paper:`, under the paper presented.
- **Papers**: edit `_data/papers.yml` (pencil icon on GitHub). To add a
  paper, copy an existing block and change the fields; the Research page,
  its jump links, the Cite panel (reference and BibTeX) and the home-page
  card (`featured: true`) follow. Sections: `publication`, `working`,
  `progress`, `other`; empty sections are not shown. A topic filter appears
  on its own from `filter_from` papers. The introduction text stays in
  `research.html`.
- **Light/dark theme**: visitors switch with the button in the header;
  the choice is remembered, otherwise the system setting is used.
- **Fonts**: Fraunces (titles), Source Serif 4 (text) and Source Sans 3
  (labels) are served from `assets/fonts/` as variable fonts under the SIL
  Open Font License; no request goes to Google Fonts.
- **CV**: edit `assets/cv/cv-source.html` (Harvard-style layout, EB Garamond
  in `assets/cv/fonts/`), open it in Chrome, print to PDF (A4, default
  margins, no browser headers/footers, background graphics on) and replace
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
