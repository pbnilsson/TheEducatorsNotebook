# Conventions

Why the site is built the way it is. `README.md` covers *how* to run the build;
this file covers the decisions a future change should not accidentally undo.

---

## Publishing

**GitHub Pages serves the committed `docs/` folder from `main`.** There is no
Action installed — `setup/github-actions-build.yml` is a template sitting in the
wrong directory, deliberately left inactive. Consequences:

- A commit that changes only `data/` changes nothing on the live site. This has
  bitten us once already.
- Every content change is: edit data → `python3 build.py` → commit **both** the
  data and the regenerated `docs/` → push.
- `build.py` wipes and regenerates `docs/` on every run. Never hand-edit inside it.

The manual arrangement is a deliberate choice: the built HTML stays visible in
the repo and in diffs, and a bad build is caught locally rather than by email.

---

## Data model

`data/articles.json` — one object per article. Two fields carry topic information
and they do **not** mean the same thing:

- `category` — the section the article printed under in that week's issue.
  Features carry `*feature` or `tech/ai: *feature` here, which means the category
  field alone does not tell you what a feature is *about*.
- `tags` — the actual topics. Hand-entered since 2013, so the vocabulary is messy
  (162 distinct raw values across the archive).

Anything that asks "what is this article about" must read `tags`, not `category`.
Topic pages once matched on `category` and silently dropped all 1,112 features.

`data/issues.json` — one object per issue, keyed by date:

| field | meaning |
|---|---|
| `number` | issue number |
| `teaser` | one-line summary for the Browse by Issue page (see below) |
| `intro_md` | the week's introduction |
| `ai_heading` / `ai_intro_md` | the A.I. Update introduction |
| `images` | issue images; the **last** one belongs to the A.I. Update section |
| `scraped`, `special` | provenance flags |

---

## Tag canonicalisation

`TAG_ALIASES` in `build.py` folds hand-entry variants into the canonical category
keys — case (`STEM`/`stem`), plurals (`assessments`), and clear typos (`pedgogy`,
`diversity/inclustion`, `sustainabtility`, `ethics and risks`). Two semantic
mappings are also in there by decision, not accident: `reading` → Reading/Writing
and `professional development` → PD.

**Fine-grained one-off tags are ignored on purpose** — `poetry`, `memory`,
`coding`, `montessori`, `shakespeare` and the like. Promoting them to real topics
would produce hundreds of groups holding one article each. Articles whose only
tags are one-offs fall into their page's own group, which is the right place for
them.

If you add a canonical topic, add it to `data/categories.json`; the alias table
only needs a new entry when a *variant spelling* appears.

---

## Issue introductions

The first line of `intro_md` and `ai_intro_md` is a header, written as `#### Text`.
`build.py`'s `md_block` renders that as `<h4 class='intro-head'>` — serif, 19px.

Three things to know:

1. **`#### ` is the only header form that works.** A line starting `- #### ` is
   not a header to the renderer; it becomes a paragraph, and because the body
   text that followed was indented 4–6 spaces it got swallowed into the same
   paragraph. That produced headers reading "…AI agents, and more An excellent
   week!" across 48 intros. Normalised in `1e1f650`; don't reintroduce the bullet.
2. **`md_block` is a deliberately tiny markdown subset** — `####`/`###` headings,
   blank-line paragraph splits, and inline links/bold/italic. Nothing else parses.
3. **Issues before #441 (2024-03-24) have no header, by design.** The convention
   didn't exist yet; their first line is prose. Ten later A.I. Update intros also
   open with prose rather than a header — left alone rather than manufactured.

---

## Teasers

The one-line summary after the date on Browse by Issue. Written for a reader
scanning the archive who wants a glimpse of what's inside.

**Sourcing, in order of priority:**

1. The issue's **features** — hand-picked, and the best signal of what mattered.
2. Any **topic cluster that is outsized** relative to the issue. The concentration
   is itself editorial information: eleven learning-science pieces in #41, nearly
   all about sleep and naps, describe that issue better than either feature does.
3. Individually striking headlines.

**Form:**

- 2–4 items, comma-separated, each 2–7 words.
- Mixed register — noun phrases and short sentences or questions, whichever fits.
- Sentence case, no trailing period.
- Concrete and named. "Nicholas Carr returns" beats "technology criticism."
- **Never** filler: no "and more", "various topics", "a range of articles".
- Prefer a short line to a padded one. Prefer `null` to a vague line — #18 and
  #515 are null because they have one article and none respectively.

**Width.** Rows do not wrap; the teaser clips with an ellipsis. The budget is
roughly **58 characters**, but character count is a proxy — what actually matters
is rendered width against a 680px column, and long dates ("September 29, 2019")
eat into it. Measure before committing a batch:

```python
from PIL import ImageFont
f17 = ImageFont.truetype("DejaVuSans.ttf", 17)   # the issue link
f15 = ImageFont.truetype("DejaVuSans.ttf", 15)   # the teaser
width = f17.getlength(label) + 7 + f15.getlength("· " + teaser)   # keep <= 680
```

DejaVu is wider than the site's actual font stack, so this errs conservative —
which is what we want.

---

## Topic pages

Each page collects every article carrying the topic (via `article_topics`, which
reads tags *and* section) and groups them by the **other** topics they are
cross-listed with. An article tagged Curriculum + Admissions + Arts appears on the
Curriculum page under both Admissions and Arts — repetition is intended, so no
connection is invisible.

**Ordering:** Featured blocks first, then alphabetical by display name
(case-insensitively — otherwise "STEM" sorts before "Social Media"), then
General / Tech-AI: Other last.

**The page's own topic** holds the articles carrying no second topic, and sits in
its normal alphabetical slot rather than being pinned. It is usually the largest
group on the page.

**Progressive reveal:** each group shows 5 articles, then a link reading
"See 20 more of N *Topic* articles in *Page*", revealing 20 at a time and
recomputing N. On the page's own group the redundant "in *Page*" is dropped. When
fewer than 20 remain the wording changes to "See N more …" — "20 more of 13"
would be nonsense.

All articles are in the HTML; `static/topics.js` hides the overflow on load. **The
page degrades to the full list without JavaScript**, which is the right failure
direction — keep it that way if you touch the script.

A two-column jump list at the top links to every group with its count.

---

## Topics index

Featured first in both lists, everything else strictly alphabetical. Counts are
computed at build time from tag-based membership, **not** from the `count` field
in `categories.json` — that field is category-based and now understates most
topics. Don't wire the page back to it.

---

## Open / deferred

- **Titles are bare.** *Hidden Figures*, *The Martian*, *Gatsby* appear without
  quotes or italics in teasers, because punctuation costs characters. Italicising
  them means a template change plus markup in the data.
- **Images point at WordPress.** `scripts/download_images.py` localises them; run
  it before retiring the WordPress site.
- **The subscribe form is a stub.** Wired up during the email-platform migration.
- **DNS cutover to educatorsnotebook.com has not happened.** See README.
