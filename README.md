# The Educator's Notebook — static site

Static rebuild of [educatorsnotebook.com](https://educatorsnotebook.com): 525 issues,
~17,000 curated articles (2013–present), generated from a single data file and
deployed to GitHub Pages on every push.

## How it works

```
data/articles.json    ← the spreadsheet (one row per article)
data/issues.json      ← per-issue editorial content (intros, A.I. Update intros, images)
data/categories.json  ← canonical category names, slugs, section assignment
build.py              ← reads the three files above, writes site/
.github/workflows/    ← builds and deploys to GitHub Pages on push
```

No dependencies — `python3 build.py` is the whole build (≈2 seconds).

## Weekly update workflow

1. Add the new issue's rows to the master spreadsheet (Numbers).
2. Export as CSV, run the converter (`scripts/csv_to_json.py`) to refresh `data/articles.json`.
3. Add the issue's intro/images to `data/issues.json` (or run the helper).
4. Commit and push. The Action rebuilds and deploys automatically (~1 minute).

## Local preview

```
python3 build.py
cd site && python3 -m http.server 8000
```

## Images

Issue images currently reference the live WordPress URLs. Run
`scripts/download_images.py` once (locally, on a machine with normal internet
access) to download all 160 images into `static/images/` and rewrite
`data/issues.json` to use local paths. Do this before retiring WordPress.

## URL compatibility

All WordPress-era URLs are preserved:
`/issues/YYYY-MM-DD` and `/topics/slug/` resolve to the same content.

## DNS cutover (when ready — not yet done)

1. In repo Settings → Pages, add custom domain `educatorsnotebook.com`.
2. At the DNS host, point the domain at GitHub Pages (A records
   185.199.108.153 / .109. / .110. / .111. and CNAME `www` → `<user>.github.io`).
3. Keep WordPress alive but unlinked for a cycle or two as fallback.
