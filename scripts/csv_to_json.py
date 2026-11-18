#!/usr/bin/env python3
"""Convert a fresh 'EdLetter Articles (YY-MM-DD).csv' export into data/articles.json.

Usage: python3 scripts/csv_to_json.py "path/to/EdLetter Articles (26-08-09).csv"

Applies the same cleaning rules as the original migration:
- date normalization (issue + pub dates to YYYY-MM-DD)
- category canonicalization (case merges, 'other'→'z-other')
- https:// prefix for bare links
- de-duplication of identical (issue, link) pairs
New categories not yet in data/categories.json are reported so you can add them.
"""
import csv, json, os, re, sys, collections
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data")

CAT_ALIASES = {"other": "z-other"}

# Pub dates that are typos in the master spreadsheet, corrected by hand
# (2026-11-18). Keyed by link; applied after parsing so a re-export keeps them.
PUB_DATE_FIXES = {
    "https://www.nytimes.com/2022/07/11/well/family/check-in-text-friendship.html": "2022-07-11",
    "https://www.theguardian.com/sport/2023/jun/21/wimbledon-introduce-ai-powered-commentary-to-coverage-this-year": "2023-06-21",
    "https://hbr.org/2008/04/can-you-say-what-your-strategy-is": "2008-04-01",
    "https://drive.google.com/file/d/1npb3gVTykW6LyieGTsx9NI4caJ1SB80d/view": "2023-08-01",
    "https://hedcoinstitute.uoregon.edu/reports/four-day-school-week-research-database": "2024-06-01",
    "https://news.stanford.edu/stories/2024/06/habitat-ceo-stanford-gsb-graduates-values-are-foundation": "2024-06-19",
    "https://sloanreview.mit.edu/article/ai-explainability-how-to-avoid-rubber-stamping-recommendations/": "2025-06-12",
    "https://www.nytimes.com/2025/10/20/technology/ai-data-center-backlash-mexico-ireland.html?smid=nytcore-ios-share&referringSource=articleShare": "2025-10-20",
    # Undated pages: Peter's convention is to use the issue date (the day he visited).
    "https://nationalhumanitiescenter.org/education-programs/webinars/": "2020-12-06",
    "http://www.pz.harvard.edu/thinking-routines": "2022-08-07"
}

def parse_date(s):
    s = (s or "").strip()
    for f in ("%d-%m-%Y", "%d/%m/%Y", "%m/%d/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    return None

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: csv_to_json.py <csv-file>")
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
    categories = json.load(open(os.path.join(DATA, "categories.json")))
    known = set(categories)
    articles, seen, new_cats = [], {}, collections.Counter()
    for r in rows:
        issue_dt = parse_date(r["Issue Date"])
        if not issue_dt:
            print("SKIP bad issue date:", r.get("Issue Date"), r.get("Headline", "")[:40])
            continue
        link = (r["Link"] or "").strip()
        if link and not re.match(r"https?://", link):
            link = "https://" + link
        cat = (r["Category"] or "").strip().lower()
        cat = CAT_ALIASES.get(cat, cat)
        if cat not in known:
            new_cats[cat] += 1
        pub_dt = parse_date(r["Pub Date"])
        art = {
            "issue": issue_dt.strftime("%Y-%m-%d"),
            "headline": (r["Headline"] or "").strip(),
            "link": link,
            "publication": (r["Publication"] or "").strip(),
            "pub_date": pub_dt.strftime("%Y-%m-%d") if pub_dt else (r["Pub Date"] or "").strip(),
            "category": cat,
            "tags": [t.strip() for t in (r["Category Tags"] or "").split(",") if t.strip()],
            "quote": (r["Quote"] or "").strip(),
        }
        if art["link"] in PUB_DATE_FIXES:
            art["pub_date"] = PUB_DATE_FIXES[art["link"]]
        key = (art["issue"], art["link"])
        if key in seen and art["link"]:
            if len(art["quote"]) > len(articles[seen[key]]["quote"]):
                articles[seen[key]] = art
            continue
        seen[key] = len(articles)
        articles.append(art)
    articles.sort(key=lambda a: (a["issue"], a["category"]))
    json.dump(articles, open(os.path.join(DATA, "articles.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"Wrote {len(articles)} articles from {len(rows)} rows.")
    if new_cats:
        print("NEW CATEGORIES (add to data/categories.json and to issues as needed):")
        for c, n in new_cats.items():
            print(f"  {c!r}: {n} articles")
        print('Template: "<cat>": {"display": "<Name>", "slug": "<slug>", "count": 0, "section": "main"}')

    # refresh counts + warn about issues.json coverage
    counts = collections.Counter(a["category"] for a in articles)
    for c in categories:
        categories[c]["count"] = counts.get(c, 0)
    json.dump(categories, open(os.path.join(DATA, "categories.json"), "w"),
              ensure_ascii=False, indent=1)
    issues = json.load(open(os.path.join(DATA, "issues.json")))
    missing = sorted(set(a["issue"] for a in articles) - set(issues))
    if missing:
        print("Issues present in CSV but not yet in data/issues.json (add entries):", missing)
        nums = sorted((v["number"], k) for k, v in issues.items())
        top = nums[-1][0]
        for i, d in enumerate(missing):
            print(f'  "{d}": {{"number": {top+1+i}, "intro_md": null, "ai_heading": null, '
                  f'"ai_intro_md": null, "images": [], "scraped": false, "special": null}}')

if __name__ == "__main__":
    main()
