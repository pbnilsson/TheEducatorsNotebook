"""Mailchimp email HTML for one issue.

Rebuilds what the WordPress site served at /issues/<date>/email/raw: a
self-contained, inline-styled HTML document that is pasted into Mailchimp as
the campaign's code. Markup and styles are copied from the email actually sent
for #533 (2026-11-15), so the emails look the same as before.

Mailchimp adds its own footer (address, unsubscribe) and rewrites links for
click tracking, so neither appears here. *|ARCHIVE|* is a Mailchimp merge tag
for the "view in browser" link.
"""
import html, re

SITE = "https://educatorsnotebook.com/"
TEAL = "#409B90"

H2 = """
        margin: 4rem 0rem 0rem 0rem;
        padding: 0;
        display: block;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: #409B90;
        font-family: sans-serif;
    """
H3 = """
        margin: 0rem 0rem 0rem 0rem;
        padding: 0;
        display: block;
        font-size: 14px;
        line-height: 1.325;
        color: #132235;
        font-family: sans-serif;
        font-weight: 600;
        display: inline-block;
    """
H3_LINK = """
        text-decoration: none;
        color: #132235;
		border-bottom: 1px solid #409B90;
    """
UL = """
        list-style: none;
        margin: 0.125rem 0rem 0rem 0rem;
        padding: 0;
        font-family: sans-serif;
        font-size: 14px;
        line-height: 1.325;
        color: #999;
        font-weight: normal;
        display: inline-block;
        font-style: italic;
    """
LI = """
        display: inline-block;
	        margin: 0 0.5rem 0 0;

    """
INTRO_DIV = """
        font-family: serif; color: black; font-size: 14px; line-height: 1.325; font-weight: 400; color: #555;
    """
QUOTE_SPAN = """
        font-family: serif; color: black; font-size: 14px; line-height: 1.325; font-weight: 400; color: #555; display: inline;
    """
P = "font-family: sans-serif; font-size: 14px; line-height: 1.325; color: #555;"
P_INLINE = "font-family: sans-serif; font-size: 14px; line-height: 1.325; display: inline; color: #555;"
A = f"text-decoration: none; color: {TEAL}; border-bottom: 1px solid {TEAL};"
HR_ROW = """                    <tr>
                        <td>
                            <hr style="border: 0; height: 2px; background-color: #D6D6D6; margin: 4rem 0rem 0rem">
                        </td>
                    </tr>
"""

LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
EM_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
EVENT_RE = re.compile(r"^\*\*[A-Z][a-z]+ \d")   # "**November 18:** ..." in a PS events list


def inline(s):
    s = html.escape(s, quote=False)
    s = LINK_RE.sub(lambda m: f'<a style="{A}" href="{m.group(2)}">{m.group(1)}</a>', s)
    s = BOLD_RE.sub(r"<b>\1</b>", s)
    s = EM_RE.sub(r"<em>\1</em>", s)
    return s


def abs_url(u):
    if not u or u.startswith(("http://", "https://", "mailto:")):
        return u
    return SITE + u.lstrip("/")


def figures(imgs):
    out = []
    for img in imgs or []:
        src = abs_url(img.get("src", ""))
        href = abs_url(img.get("href")) or src
        cap = img.get("caption")
        cap_html = f'<figcaption style="{P}">{inline(cap)}</figcaption>' if cap else ""
        out.append(
            f'<figure style="width: 500px; max-width: 100%; margin: 1rem auto;">'
            f'<a style="text-decoration: none; color: {TEAL};" href="{html.escape(href, quote=True)}">'
            f'<img src="{html.escape(src, quote=True)}" alt="" width="500" '
            f'style="display: block; width: 100%; max-width: 500px; height: auto; border: 0;"></a>'
            f'{cap_html}</figure>')
    return "\n".join(out)


def intro_block(md, imgs, footer_html=""):
    """Header line (#### ...) as the bold heading, paragraphs below, then the
    images. A PS events list is tightened so each date line and its
    description share one paragraph (joined by <br>), as Peter edits it by hand."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", (md or "").strip()) if p.strip()]
    head = ""
    if paras and paras[0].startswith(("#### ", "### ")):
        head = paras.pop(0).split(" ", 1)[1].strip()
    merged, i = [], 0
    while i < len(paras):
        p = "<br>\n".join(inline(l.strip()) for l in paras[i].splitlines())
        if EVENT_RE.match(paras[i]) and "\n" not in paras[i] and i + 1 < len(paras) \
                and not EVENT_RE.match(paras[i + 1]) \
                and not paras[i + 1].lower().lstrip("*").startswith("later events"):
            nxt = "<br>\n".join(inline(l.strip()) for l in paras[i + 1].splitlines())
            merged.append(p + "<br>\n" + nxt)
            i += 2
        else:
            merged.append(p)
            i += 1
    body = "\n".join(f'<p style="{P}">{p}</p>' for p in merged)
    body += ("\n" + figures(imgs)) if imgs else ""
    body += footer_html
    h3 = f'<h3 style="{H3}">{inline(head)}</h3>' if head else ""
    return f'<div style="margin-top: 1.25rem">{h3}<div style="{INTRO_DIV}">{body}\n</div></div>'


def article(a):
    q = a.get("quote") or ""
    qhtml = f'<p style="{P_INLINE}">{html.escape(q, quote=False)}</p>\n' if q else ""
    return (f'<div style="margin-top: 1.25rem"><h3 style="{H3}"><a style="{H3_LINK}" '
            f'href="{html.escape(a["link"], quote=True)}">{html.escape(a["headline"], quote=False)}</a></h3>\n'
            f'            <ul style="{UL}">\n'
            f'                <li style="{LI}">{html.escape(a["publication"], quote=False)}</li>\n'
            f'            </ul><span style="{QUOTE_SPAN}">{qhtml}</span></div>')


def row(inner):
    return f"""
                                    <tr>
                        <td>
                            {inner}                        </td>
                    </tr>
"""


def h2(text):
    return f'<h2 style="{H2}">{html.escape(text, quote=False)}</h2>'


def render(d, meta, arts, categories, order_categories, fmt_date, total_articles):
    cats_present = sorted(set(a["category"] for a in arts))
    main_cats = order_categories(cats_present, "main")
    ai_cats = order_categories(cats_present, "ai")
    imgs = meta.get("images") or []
    has_ai = bool(ai_cats or meta.get("ai_intro_md"))
    ai_imgs = imgs[-1:] if (has_ai and imgs) else []
    intro_imgs = imgs[:-1] if (has_ai and imgs) else imgs
    n = meta["number"]
    browse = f"{total_articles // 1000:,},000" if total_articles >= 1000 else str(total_articles)

    footer = (f'\n<p style="{P}">&nbsp;</p>\n<hr>\n<p style="{P}">&nbsp;</p>\n'
              f'<p style="text-align: center;">Browse and search over {browse} curated articles from '
              f'<a style="{A}" href="{SITE}issues/">past issues online</a>:</p>\n'
              f'<p style="text-align: center;"><a style="{A}" href="{SITE}subscribe/">'
              f'Subscribe to the Educator’s Notebook</a></p>')

    rows = []
    if meta.get("intro_md") or intro_imgs:
        rows.append(row(h2("Introduction") + intro_block(meta.get("intro_md"), intro_imgs, footer)))
    else:
        rows.append(row(intro_block("", [], footer)))
    rows.append(HR_ROW)
    for c in main_cats:
        rows.append(row(h2(categories[c]["display"]) +
                        "".join(article(a) for a in arts if a["category"] == c)))
        if c == "*feature":
            rows.append(HR_ROW)
    if has_ai:
        rows.append(HR_ROW)
        rows.append(row(h2("A.I. Update")))
        if meta.get("ai_intro_md") or ai_imgs:
            ai_intro = intro_block(meta.get("ai_intro_md"), ai_imgs, f'\n<p style="{P}">&nbsp;</p>')
            rows.append(row(ai_intro))
        for c in ai_cats:
            rows.append(row(h2(categories[c]["display"]) +
                            "".join(article(a) for a in arts if a["category"] == c)))

    return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">


<p style="text-align: center">
    <a href="*|ARCHIVE|*" style="font-family: sans-serif; font-size: 14px; font-weight: bold; color: {TEAL}">
        View this email in your browser
    </a>
</p>
<table style="width:100%; height: 100%;" cellpadding="0" cellspacing="0">
    <tr>
        <td style="text-align: center" align="center">

            <table style="max-width: 600px; width: 100%; margin: auto; text-align: left">
                <tr>
                    <td style="background-color: {TEAL}; text-align: center; padding: 2.5rem 1.5rem;">

			                        	<h1 style="margin: 0rem 0rem 0rem; padding: 0; font-family: serif; color: white; font-size: 40px; line-height: 1.325">
				                        	The Educator's Notebook
			                        	</h1>
			                        	<p style="text-align: center; color: white; margin: 0rem; font-family: sans-serif; font-size: 16px; font-style: italic; font-weight: normal;">
				                        	A weekly collection of education-related news from around the web.
			                        	</p>
			                        	<p style="text-align: center; color: white; margin: 2rem 0rem 0rem; font-family: sans-serif; font-size: 16px; font-weight: bold;">
				                            {fmt_date(d)} (#{n})			                        	</p>

                    </td>
                </tr>
{"".join(rows)}

            	</table>

        </td>
    </tr>
</table>
"""


def raw_page(d, n, code, fmt_date):
    """The /email/raw/ page: the code in a box with a Copy button."""
    esc = html.escape(code, quote=False)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Email HTML — #{n} ({fmt_date(d)})</title>
<style>
 body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; margin: 2rem auto; max-width: 900px; padding: 0 1rem; color: #222; }}
 h1 {{ font-size: 20px; margin: 0 0 .5rem; }}
 p {{ margin: .25rem 0 1rem; color: #555; }}
 button {{ font-size: 15px; padding: .5rem 1.1rem; background: #1b4a7a; color: #fff; border: 0; border-radius: 4px; cursor: pointer; }}
 #done {{ margin-left: .75rem; color: #2a7d3f; }}
 textarea {{ width: 100%; height: 70vh; margin-top: 1rem; font: 12px/1.4 Menlo, Consolas, monospace; box-sizing: border-box; }}
 a {{ color: #1b4a7a; }}
</style></head><body>
<h1>Email HTML for Educator&rsquo;s Notebook #{n} ({fmt_date(d)})</h1>
<p>Copy this into Mailchimp (Code your own). <a href="../">Preview the email</a> &middot; <a href="../../">Issue page</a></p>
<button onclick="navigator.clipboard.writeText(document.getElementById('code').value).then(function(){{document.getElementById('done').textContent='Copied.'}})">Copy HTML</button><span id="done"></span>
<textarea id="code" readonly onclick="this.select()">{esc}</textarea>
</body></html>
"""
