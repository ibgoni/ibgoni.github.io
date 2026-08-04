# Academic Website — Ibrahim Goni Abdoulkadiri

Personal academic website of Ibrahim Goni Abdoulkadiri, Ph.D. candidate in
development economics at CERDI (Université Clermont Auvergne, CNRS, IRD).

Live site: https://ibgoni.github.io/

Static HTML and CSS, no build step for the site itself. Deployed with GitHub
Pages: every change merged into `main` is live about a minute later (allow up to
10 minutes for the HTTP cache). Notebooks are the one thing that is generated,
and GitHub does that for you — see below.

## Pages

| File | Page |
| --- | --- |
| `index.html` | Home — profile, interests, education, featured paper, news |
| `research.html` | Working papers and projects, with filters and BibTeX |
| `notebooks.html` | Index of published notebooks — **generated, do not edit** |
| `notebooks/<name>.html` | One page per notebook — **generated, do not edit** |
| `teaching.html` | Teaching |
| `404.html` | Not-found page |

Supporting files:

- `assets/css/style.css` — the whole site design
- `assets/css/notebook.css` — notebook pages only
- `assets/js/site.js` — theme toggle, mobile menu, filters, BibTeX copy
- `assets/cv/Ibrahim_Goni_CV.pdf` — downloadable CV
- `assets/img/portrait.jpg` — profile photo
- `tools/` — the notebook publishing pipeline
- `sitemap.xml`, `robots.txt`, `.nojekyll`

## Publishing a Jupyter notebook

This is the part that answers "can I put my analyses on the site?" — yes, and
the only thing you do is add the `.ipynb` file.

1. Write your notebook and **run it, so the outputs are saved in the file**.
2. Make the *first* cell a **raw cell** containing the description:

   ```
   ---
   title: What the notebook is about
   date: 2026-07-28
   summary: One or two sentences. Shown on the notebooks index and used as the
     page description for Google. It can run over several lines like this.
   tags: [difference-in-differences, python]
   draft: false
   ---
   ```

   Everything is optional. Without a `title` the first `# heading` is used;
   without a `date`, the date of the commit. `draft: true` keeps a notebook in
   the repository without publishing it.
3. Drop the file into `notebooks/` and push (or upload it through the GitHub web
   interface — *Add file → Upload files*).
4. A GitHub Action converts it and commits the generated pages. The notebook
   appears on `notebooks.html` about a minute later.

### Controlling what the reader sees

Add these **cell tags** in Jupyter (*View → Cell Toolbar → Tags*):

| Tag | Effect |
| --- | --- |
| `hide-input` | Hides the code, keeps the output — good for setup cells |
| `hide-output` | Keeps the code, hides the output |
| `remove-cell` | Drops the cell entirely |

Maths written as `$...$` or `$$...$$` in markdown cells is typeset on the page.
The reader gets a *Download .ipynb* link, so the notebook stays reproducible.

### Building locally (optional)

```bash
pip install nbformat nbconvert
python3 tools/build_notebooks.py            # convert, using the saved outputs
python3 tools/build_notebooks.py --execute  # re-run the notebooks first
python3 tools/build_notebooks.py --check    # fail if the HTML is out of date
python3 tools/test_build_notebooks.py       # tests for the pipeline
```

To preview the site, serve it rather than opening the files directly — links are
absolute, so `file://` will not resolve them:

```bash
python3 -m http.server 8000    # then open http://localhost:8000
```

## Updating the rest of the site

- **Text or a new paper**: edit the relevant HTML file (e.g. `research.html`)
  directly on GitHub (pencil icon). To add a paper, copy an existing
  `<article class="paper" data-status="...">…</article>` block and edit the text
  inside the tags. Keep `data-status` set to `working-paper`, `in-progress`, or
  `other` — that is what the filter buttons use, and the counts update by
  themselves.
- **CV**: edit `assets/cv/cv-source.html`, open it in Chrome, print to PDF (A4,
  default margins, no browser headers/footers) and replace
  `assets/cv/Ibrahim_Goni_CV.pdf`. Full instructions are in a comment at the top
  of the source file.
- **Photo**: replace `assets/img/portrait.jpg` (keep the same filename).
- **The notebook card on the home page** is written by hand, so it can be
  featured. If you change a notebook's summary, update that card too — or just
  delete the card and let `notebooks.html` be the only listing.
- Remember to update the "Last updated" date in the footer of each page.

## Design notes

The layout follows the block structure of the Hugo Blox *Academic CV* template
(profile hero, interests and education cards, filterable publications, notebook
grid) but is hand-written, so there is no framework to upgrade and nothing that
can fail to build.

Colours are checked against WCAG AA in both themes. Two of them exist for that
reason and should not be collapsed: `--gold` is decorative only (rules, markers,
borders), and `--gold-text` is the darker variant used wherever gold carries
text. The dark palette is written twice on purpose — once behind
`prefers-color-scheme` for the first paint and for visitors without JavaScript,
once behind `[data-theme="dark"]` for the toggle. **Keep the two blocks in
sync.**

## Two things worth doing when you have time

- **Host the working-paper PDFs here** instead of Dropbox
  (`assets/papers/wired-for-growth.pdf`). Then each paper can get its own page
  carrying Google Scholar's `citation_title` / `citation_author` /
  `citation_pdf_url` tags, which is how Scholar indexes a personal site. Those
  tags only work with one paper per page and a PDF it can actually fetch, so
  they were left out rather than added in a form that would not work.
- **Add your ORCID and Google Scholar profiles** to the social row on
  `index.html` and to `sameAs` in the JSON-LD block, once you have the URLs.
