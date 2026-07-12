# Academic Website — Ibrahim Goni Abdoulkadiri

Personal academic website of Ibrahim Goni Abdoulkadiri, Ph.D. candidate in
development economics at CERDI (Université Clermont Auvergne, CNRS, IRD).

Live site: https://ibgoni.github.io/

## Structure

- `index.html` — home page (bio, photo, contact)
- `research.html` — working papers and work in progress, with expandable abstracts
- `teaching.html` — teaching
- `assets/cv/Ibrahim_Goni_CV.pdf` — downloadable CV
- `assets/css/style.css` — shared stylesheet
- `assets/img/portrait.jpg` — profile photo

Static HTML/CSS only, no build step. Deployed with GitHub Pages: every
change merged into `main` is live about a minute later (allow up to
10 minutes for the HTTP cache).

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
- Remember to update the "Last updated" date in the footer of each page.
