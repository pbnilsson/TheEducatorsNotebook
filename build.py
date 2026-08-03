#!/usr/bin/env python3
"""Static site generator for The Educator's Notebook.

Reads data/articles.json, data/issues.json, data/categories.json
and writes the complete site into site/.

Usage: python3 build.py
No third-party dependencies.
"""
import json, os, re, html, shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "site")
STATIC = os.path.join(HERE, "static")

SITE_TITLE = "The Educator's Notebook"
TAGLINE = "A weekly collection of education-related news from around the web."

# ---------------------------------------------------------------- tiny markdown
LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")

def md_inline(s):
    s = html.escape(s, quote=False)
    s = LINK_RE.sub(r'<a href="\2">\1</a>', s)
    s = BOLD_RE.sub(r"<strong>\1</strong>", s)
    s = EM_RE.sub(r"<em>\1</em>", s)
    return s

def md_block(md):
    """Paragraph-level markdown: #### headings, paragraphs, blank-line splits."""
    if not md:
        return ""
    out = []
    for para in re.split(r"\n\s*\n", md.strip()):
        p = para.strip()
        if not p:
            continue
        if p.startswith("#### "):
            out.append(f"<h4 class='intro-head'>{md_inline(p[5:].strip())}</h4>")
        elif p.startswith("### "):
            out.append(f"<h4 class='intro-head'>{md_inline(p[4:].strip())}</h4>")
        else:
            p = " ".join(line.strip() for line in p.splitlines())
            out.append(f"<p>{md_inline(p)}</p>")
    return "\n".join(out)

# ---------------------------------------------------------------- data
articles = json.load(open(os.path.join(DATA, "articles.json")))
issues = json.load(open(os.path.join(DATA, "issues.json")))
categories = json.load(open(os.path.join(DATA, "categories.json")))

by_issue = {}
for a in articles:
    by_issue.setdefault(a["issue"], []).append(a)
issue_dates = sorted(issues.keys())

def fmt_date(d, fmt="%B %-d, %Y"):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime(fmt)
    except ValueError:
        return d

def fmt_pubdate(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d/%y")
    except ValueError:
        return d

# ---------------------------------------------------------------- layout
def page(rel, title, body, desc=None):
    """rel = path prefix back to root ('' or '../' etc.)"""
    desc = html.escape(desc or TAGLINE, quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{desc}">
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<header class="masthead">
  <a class="site-title" href="{rel}index.html">{SITE_TITLE}</a>
  <p class="tagline">{TAGLINE}</p>
  <nav>
    <a href="{rel}index.html">Current Issue</a>
    <a href="{rel}issues/index.html">Browse by Issue</a>
    <a href="{rel}topics/index.html">Browse by Topic</a>
    <a href="{rel}search/index.html">Search</a>
    <a href="{rel}subscribe/index.html">Subscribe</a>
  </nav>
</header>
<main>
{body}
</main>
<footer>
  <p><a href="{rel}subscribe/index.html">Subscribe to the Educator&rsquo;s Notebook</a> &middot; Curated weekly by <a href="http://www.peternilsson.us/">Peter Nilsson</a> since 2013. All rights reserved.</p>
</footer>
</body>
</html>"""

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# ---------------------------------------------------------------- issue body
def order_categories(cats_present, section):
    """feature first, z-other last, alphabetical between."""
    def key(c):
        if c in ("*feature", "tech/ai: *feature"):
            return (0, "")
        if c in ("z-other", "tech/ai: z-other"):
            return (2, "")
        return (1, c)
    return sorted([c for c in cats_present if categories[c]["section"] == section], key=key)

def article_entry(a):
    q = f'\n  <blockquote>{html.escape(a["quote"], quote=False)}</blockquote>' if a["quote"] else ""
    pub = html.escape(a["publication"], quote=False)
    return f"""<div class="entry">
  <h4><a href="{html.escape(a["link"], quote=True)}">{html.escape(a["headline"], quote=False)}</a></h4>
  <p class="meta">{pub} &middot; {fmt_pubdate(a["pub_date"])}</p>{q}
</div>"""

def issue_images_html(imgs, rel):
    out = []
    for img in imgs or []:
        src = img.get("src", "")
        cap = img.get("caption")
        href = img.get("href") or src
        cap_html = f"<figcaption>{md_inline(cap)}</figcaption>" if cap else ""
        out.append(f"""<figure><a href="{html.escape(href, quote=True)}"><img src="{html.escape(src, quote=True)}" alt="{html.escape(cap or '', quote=True)}" loading="lazy"></a>{cap_html}</figure>""")
    return "\n".join(out)

def issue_body(d, rel):
    meta = issues[d]
    arts = by_issue.get(d, [])
    cats_present = sorted(set(a["category"] for a in arts))
    n = meta["number"]
    prev_d = issue_dates[issue_dates.index(d) - 1] if issue_dates.index(d) > 0 else None
    next_d = issue_dates[issue_dates.index(d) + 1] if issue_dates.index(d) < len(issue_dates) - 1 else None
    nav = "<p class='issue-nav'>"
    if prev_d:
        nav += f"<a href='{rel}issues/{prev_d}/index.html'>&larr; Previous Issue</a>"
    if prev_d and next_d:
        nav += " &middot; "
    if next_d:
        nav += f"<a href='{rel}issues/{next_d}/index.html'>Next Issue &rarr;</a>"
    nav += "</p>"

    imgs = meta.get("images") or []
    ai_cats = order_categories(cats_present, "ai")
    has_ai = bool(ai_cats or meta.get("ai_intro_md"))
    # The final scraped image belongs at the end of the A.I. Update text,
    # ahead of the A.I. Update articles. Everything before it stays in the intro.
    ai_imgs = imgs[-1:] if (has_ai and imgs) else []
    intro_imgs = imgs[:-1] if (has_ai and imgs) else imgs

    parts = [f"<h1>Educator&rsquo;s Notebook #{n} ({fmt_date(d)})</h1>", nav]
    if meta.get("intro_md"):
        parts.append("<section class='intro'><h3>Introduction</h3>")
        parts.append(md_block(meta["intro_md"]))
        parts.append(issue_images_html(intro_imgs, rel))
        parts.append("</section>")
    for c in order_categories(cats_present, "main"):
        parts.append(f"<h3 class='cat'>{html.escape(categories[c]['display'].upper())}</h3>")
        parts.extend(article_entry(a) for a in arts if a["category"] == c)
    if has_ai:
        parts.append("<hr><h2 class='ai-part'>A.I. Update</h2>")
        if meta.get("ai_intro_md") or ai_imgs:
            parts.append("<section class='intro'>")
            if meta.get("ai_intro_md"):
                parts.append(md_block(meta["ai_intro_md"]))
            parts.append(issue_images_html(ai_imgs, rel))
            parts.append("</section>")
        for c in ai_cats:
            parts.append(f"<h3 class='cat'>{html.escape(categories[c]['display'].upper())}</h3>")
            parts.extend(article_entry(a) for a in arts if a["category"] == c)
    parts.append(nav)
    return "\n".join(parts)

# ---------------------------------------------------------------- build
def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(STATIC, os.path.join(OUT, "assets"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    # issue pages
    for d in issue_dates:
        n = issues[d]["number"]
        write(f"issues/{d}/index.html",
              page("../../", f"Educator's Notebook #{n} ({fmt_date(d)})",
                   issue_body(d, "../../"),
                   desc=f"Issue #{n} of the Educator's Notebook, {fmt_date(d)}."))

    # home = latest issue
    latest = issue_dates[-1]
    write("index.html", page("", f"{SITE_TITLE} — #{issues[latest]['number']}",
                             issue_body(latest, "")))

    # issues index, grouped by year desc
    rows = []
    years = {}
    for d in reversed(issue_dates):
        years.setdefault(d[:4], []).append(d)
    for y in sorted(years, reverse=True):
        rows.append(f"<h3>{y}</h3><ul class='issue-list'>")
        for d in years[y]:
            n = issues[d]["number"]
            note = " — update" if issues[d].get("special") else ""
            rows.append(f"<li><a href='{d}/index.html'>#{n} &middot; {fmt_date(d)}</a>{note}</li>")
        rows.append("</ul>")
    write("issues/index.html", page("../", f"Browse by Issue — {SITE_TITLE}",
                                    "<h1>Issues</h1>\n" + "\n".join(rows)))

    # topic pages
    for c, info in categories.items():
        arts = [a for a in articles if a["category"] == c]
        arts.sort(key=lambda a: a["issue"], reverse=True)
        parts = [f"<h1>{html.escape(info['display'])}</h1>",
                 f"<p class='meta'>{len(arts)} articles</p>"]
        cur = None
        for a in arts:
            if a["issue"] != cur:
                cur = a["issue"]
                parts.append(f"<h3 class='cat'><a href='../../issues/{cur}/index.html'>#{issues[cur]['number']} &middot; {fmt_date(cur)}</a></h3>")
            parts.append(article_entry(a))
        write(f"topics/{info['slug']}/index.html",
              page("../../", f"{info['display']} — {SITE_TITLE}", "\n".join(parts)))

    # topics index
    main = [c for c in categories if categories[c]["section"] == "main"]
    ai = [c for c in categories if categories[c]["section"] == "ai"]
    def topic_li(c):
        i = categories[c]
        return f"<li><a href='{i['slug']}/index.html'>{html.escape(i['display'])}</a> <span class='meta'>({i['count']})</span></li>"
    body = ["<h1>Topics</h1><ul class='topic-list'>"]
    body += [topic_li(c) for c in sorted(main, key=lambda c: categories[c]["display"])]
    body.append("</ul><h2>A.I. Update</h2><ul class='topic-list'>")
    body += [topic_li(c) for c in sorted(ai, key=lambda c: categories[c]["display"])]
    body.append("</ul>")
    write("topics/index.html", page("../", f"Browse by Topic — {SITE_TITLE}", "\n".join(body)))

    # search page + index
    idx = [{"h": a["headline"], "p": a["publication"], "c": categories[a["category"]]["display"],
            "s": categories[a["category"]]["slug"], "d": a["issue"], "l": a["link"],
            "n": issues[a["issue"]]["number"]} for a in articles]
    write("search/search-index.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
    search_body = """<h1>Search</h1>
<p class="meta">Search %d curated articles from %d issues, 2013&ndash;present.</p>
<input type="search" id="q" placeholder="Search headlines, publications, topics&hellip;" autofocus>
<div id="results"></div>
<script src="../assets/search.js"></script>""" % (len(articles), len(issue_dates))
    write("search/index.html", page("../", f"Search — {SITE_TITLE}", search_body))

    # subscribe
    write("subscribe/index.html", page("../", f"Subscribe — {SITE_TITLE}", """
<h1>Subscribe</h1>
<p>Get the Educator&rsquo;s Notebook in your inbox each week &mdash; a curated collection of education-related news from around the web.</p>
<!-- SUBSCRIBE-FORM: replace with EmailOctopus embed during email migration -->
<form method="post" action="#" class="subscribe-form" onsubmit="alert('Form will be connected during the email-platform migration.'); return false;">
  <label>Email Address *<input type="email" name="email" required></label>
  <label>First Name<input type="text" name="fname"></label>
  <label>Last Name<input type="text" name="lname"></label>
  <label>School or organization<input type="text" name="org"></label>
  <button type="submit">Subscribe</button>
</form>
<p class="meta">&ndash; <a href="http://www.peternilsson.us/">Peter Nilsson</a></p>"""))

    # 404
    write("404.html", page("/", f"Not found — {SITE_TITLE}",
                           "<h1>Page not found</h1><p><a href='/'>Return to the current issue</a> or <a href='/issues/'>browse the archive</a>.</p>"))

    n_pages = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"Built {n_pages} files → {OUT}")

if __name__ == "__main__":
    build()
