# The Educator's Notebook — static site

Static rebuild of [educatorsnotebook.com](https://educatorsnotebook.com): 525 issues,
~17,000 curated articles (2013–present), generated from a single data file and
served by GitHub Pages from the committed `docs/` folder.

## How it works

```
data/articles.json    ← the spreadsheet (one row per article)
data/issues.json      ← per-issue editorial content (intros, A.I. Update intros, images)
data/categories.json  ← canonical category names, slugs, section assignment
build.py              ← reads the three files above, writes docs/
docs/                 ← the generated site. GitHub Pages serves this folder
                        from main (Settings → Pages → Branch: main /docs)
```

No dependencies — `python3 build.py` is the whole build (≈2 seconds).

See **[CONVENTIONS.md](CONVENTIONS.md)** for the editorial and structural rules
behind the build — teaser style, topic grouping, tag handling, intro headers.

## Weekly update workflow

1. Add the new issue's rows to the master spreadsheet (Numbers).
2. Export as CSV, run the converter (`scripts/csv_to_json.py`) to refresh `data/articles.json`.
3. Add the issue's intro/images to `data/issues.json` (or run the helper).
4. Run `python3 build.py` — this regenerates `docs/`.
5. Commit **both** the data change and the regenerated `docs/`, then push.

> **Always commit `docs/`.** GitHub Pages serves the committed `docs/` folder,
> not a build artifact — there is no Action installed (`setup/github-actions-build.yml`
> is a template, not active). A data-only commit changes nothing on the live site.
> `build.py` writes straight into `docs/`; it wipes and regenerates the folder each
> run, so never hand-edit anything inside it.

## Local preview

```
python3 build.py
cd docs && python3 -m http.server 8000
```

## Images

All issue images are served from the repo — nothing points at WordPress.
They live in `static/images/` (the build copies them to `docs/assets/images/`)
as WebP, resized to at most 1400px on the long side. In `data/issues.json` an
image's `src` is `assets/images/<name>.webp`, relative to the site root;
`build.py` adds the right `../` prefix per page.

Full-size originals are archived outside the repo, in
`EdNewsletter/Issues/Website Images/` with a `manifest.csv` mapping each file
to its issue. For a new issue: save the image as WebP (≤1400px) into
`static/images/` named `YYYY-MM-<name>.webp`, and reference it as above.

## Email HTML for Mailchimp

Replaces WordPress's `/issues/<date>/email/raw`. For the 12 most recent issues
(`EMAIL_ISSUES` in `build.py`) the build writes:

- `/issues/<date>/email/raw/` — the email's HTML in a box with a **Copy HTML** button. Paste into Mailchimp (Code your own).
- `/issues/<date>/email/` — the same HTML rendered, to preview the email.

Markup and inline styles come from `email_template.py`, copied from the email
actually sent for #533. Images and links use absolute https://educatorsnotebook.com URLs.

## URL compatibility

All WordPress-era URLs are preserved:
`/issues/YYYY-MM-DD` and `/topics/slug/` resolve to the same content.

## DNS cutover (when ready — not yet done)

1. In repo Settings → Pages, add custom domain `educatorsnotebook.com`.
2. At the DNS host, point the domain at GitHub Pages (A records
   185.199.108.153 / .109. / .110. / .111. and CNAME `www` → `<user>.github.io`).
3. Keep WordPress alive but unlinked for a cycle or two as fallback.

## Visit notes (stats)

Private stats page at `/stats/` (noindex, not linked), same design as the
peternilsson.us, Schooled and Childhood Recovery stats pages, plus an
**Issues** section: for each issue, all-time visitors, how many of them clicked
at least one link, and every article's clicks, most clicked first.

- `static/notes.js` — the tracker, loaded by every page (copied to `docs/assets/`).
  Reports views, link clicks, signups, and how far people read. Issue pages and
  the home page carry `<body data-issue="YYYY-MM-DD">`, so every view and click
  is tagged with its issue. No cookies, no personal data.
- `collector/` — the Cloudflare Worker (`ednotebook-notes`) and its D1 table.
- `.github/workflows/visit-notes.yml` — pulls rows from the collector twice a day.
  Skips quietly until the repo secret `EDNOTEBOOK_NOTES_KEY` exists.
- `scripts/visits/split-days.js` → `visits/days/*.json`;
  `scripts/visits/build-summary.js` → `visits/summary.json`. The workflow copies it to
  `docs/stats/summary.json`; `build.py` does the same on every build.
- The stats page source is `static/stats.html` (build writes it to `docs/stats/index.html`).
- Silence your own browsers by loading any page once with `?notrack=1` (Chrome, Safari, phone).
