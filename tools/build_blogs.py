#!/usr/bin/env python3
"""Generate standalone static HTML blog pages from blogs/*.md.

Run this before `flet build web`:
    python tools/build_blogs.py

For a site hosted below a path, keep --base-path in sync with Flet's --base-url:
    python tools/build_blogs.py --base-path /portfolio/
    flet build web --base-url /portfolio/
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from blog_utils import parse_blog_post, public_post_metadata  # noqa: E402

SOURCE_DIR = ROOT / "blogs"
ASSETS_DIR = ROOT / "assets"
BLOG_ASSETS_DIR = ASSETS_DIR / "blog"
MANIFEST_DIR = ASSETS_DIR / "blogs"
MANIFEST_PATH = MANIFEST_DIR / "index.json"
VALID_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*\.md$")


PAGE_CSS = r"""
:root {
  color-scheme: dark;
  --bg: #070b18;
  --panel: #10182b;
  --panel-2: #131e35;
  --line: #263451;
  --ink: #eef1fa;
  --muted: #a4aec8;
  --accent: #70a5ff;
  --accent-soft: rgba(112,165,255,.13);
  --content: 790px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  background: radial-gradient(ellipse at 82% -15%, rgba(56,93,170,.18), transparent 38%), var(--bg);
  color: var(--ink);
  font: 16px/1.7 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.site-header {
  border-bottom: 1px solid rgba(143,164,207,.15);
  background: rgba(7,11,24,.86);
  backdrop-filter: blur(16px);
}
.header-inner, .page-shell, .site-footer {
  width: min(1120px, calc(100% - 40px));
  margin: 0 auto;
}
.header-inner {
  min-height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.brand { color: var(--ink); font-weight: 750; letter-spacing: -.03em; }
.brand-mark { color: var(--accent); margin-right: 9px; }
.header-links { display: flex; gap: 22px; align-items: center; font-size: 14px; }
.header-links a { color: var(--muted); }
.page-shell { padding: 54px 0 76px; }
.breadcrumb { color: var(--muted); font-size: 13px; margin-bottom: 26px; }
.article-header { max-width: var(--content); margin: 0 auto 34px; }
.eyebrow { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; color: var(--muted); font-size: 13px; }
.article-header h1 { font-size: clamp(2.25rem, 6vw, 3.6rem); line-height: 1.12; letter-spacing: -.045em; margin: 18px 0 16px; }
.lead { color: #c3cde3; font-size: clamp(1.05rem, 2vw, 1.2rem); line-height: 1.65; margin: 0; }
.tags { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 22px; }
.tag { display: inline-block; padding: 3px 10px; border: 1px solid var(--line); border-radius: 999px; color: #c0cbe4; font-size: 12px; }
.article-layout { display: grid; grid-template-columns: minmax(0, var(--content)) 220px; gap: 52px; justify-content: center; align-items: start; }
.prose { min-width: 0; color: #cbd4e8; overflow-wrap: anywhere; }
.prose h2, .prose h3, .prose h4 { color: var(--ink); line-height: 1.25; letter-spacing: -.025em; margin: 2.1em 0 .7em; }
.prose h2 { font-size: 1.8rem; }
.prose h3 { font-size: 1.35rem; }
.prose h4 { font-size: 1.1rem; }
.prose p { margin: 0 0 1.25em; }
.prose ul, .prose ol { padding-left: 1.5em; margin: 0 0 1.3em; }
.prose li { padding-left: .25em; margin: .35em 0; }
.prose blockquote { margin: 1.5em 0; padding: .2em 0 .2em 1.15em; border-left: 3px solid var(--accent); color: #b9c7e4; }
.prose hr { border: 0; border-top: 1px solid var(--line); margin: 2.2em 0; }
.prose img { display: block; max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--line); margin: 1.5em auto; }
.prose table { width: 100%; border-collapse: collapse; display: block; overflow-x: auto; margin: 1.5em 0; font-size: .92rem; }
.prose th, .prose td { border: 1px solid var(--line); padding: 9px 12px; text-align: left; }
.prose th { background: var(--panel-2); color: var(--ink); }
.prose tr:nth-child(even) { background: rgba(255,255,255,.025); }
.prose code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .88em; background: rgba(112,165,255,.12); color: #cfe0ff; padding: .15em .38em; border-radius: 5px; }
.prose pre { overflow-x: auto; padding: 20px; border: 1px solid var(--line); border-radius: 12px; background: #0b1222; line-height: 1.55; margin: 1.5em 0; }
.prose pre code { background: none; color: inherit; padding: 0; font-size: .86rem; }
.codehilite { overflow-x: auto; margin: 1.5em 0; border: 1px solid var(--line); border-radius: 12px; background: #0b1222; }
.codehilite pre { border: 0; margin: 0; border-radius: 12px; }
.codehilite .hll { background: #263451; }
.codehilite .c, .codehilite .c1, .codehilite .cm { color: #8795b3; }
.codehilite .k, .codehilite .kn, .codehilite .kd { color: #c792ea; }
.codehilite .s, .codehilite .s1, .codehilite .s2 { color: #c3e88d; }
.codehilite .nf, .codehilite .na { color: #82aaff; }
.toc { position: sticky; top: 24px; padding: 17px; border: 1px solid var(--line); border-radius: 12px; background: rgba(16,24,43,.7); }
.toc h2 { color: var(--ink); font-size: 13px; margin: 0 0 10px; }
.toc ul { margin: 0; padding-left: 16px; list-style: none; }
.toc li { margin: 7px 0; line-height: 1.4; }
.toc a { color: var(--muted); font-size: 12px; }
.toc a:hover { color: var(--accent); }
.toc ul ul { padding-left: 12px; }
.archive-heading { max-width: 820px; margin: 0 auto 28px; }
.archive-heading h1 { font-size: clamp(2.2rem, 6vw, 3.1rem); line-height: 1.1; letter-spacing: -.04em; margin: 0 0 12px; }
.archive-heading p { color: var(--muted); margin: 0; }
.post-list { max-width: 820px; margin: 0 auto; display: grid; gap: 14px; }
.post-card { display: block; padding: 22px 24px; background: linear-gradient(145deg, rgba(19,30,53,.95), rgba(16,24,43,.92)); border: 1px solid var(--line); border-radius: 14px; color: var(--ink); transition: border-color .18s ease, transform .18s ease; }
.post-card:hover { border-color: #5576b2; transform: translateY(-2px); text-decoration: none; }
.post-card h2 { font-size: 1.25rem; line-height: 1.35; margin: 10px 0 8px; }
.post-card p { color: var(--muted); margin: 0; }
.post-meta { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; color: var(--muted); font-size: 12px; }
.read-link { color: var(--accent); font-size: 13px; margin-top: 14px; display: inline-block; }
.empty-state { max-width: 820px; margin: 0 auto; border: 1px dashed var(--line); border-radius: 14px; padding: 30px; color: var(--muted); }
.site-footer { border-top: 1px solid rgba(143,164,207,.15); padding: 24px 0 34px; color: var(--muted); font-size: 13px; display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
@media (max-width: 900px) { .article-layout { grid-template-columns: minmax(0, var(--content)); } .toc { position: static; grid-row: 1; } }
@media (max-width: 600px) {
  .header-inner, .page-shell, .site-footer { width: min(100% - 28px, 1120px); }
  .header-inner { min-height: 62px; }
  .header-links { gap: 13px; font-size: 12px; }
  .page-shell { padding: 34px 0 52px; }
  .post-card { padding: 18px; }
  .prose pre { padding: 14px; }
}
"""


def normalize_base_path(value: str) -> str:
    value = value.strip()
    if not value:
        return "/"
    if not value.startswith("/"):
        value = "/" + value
    if not value.endswith("/"):
        value += "/"
    return value


def read_posts() -> list[dict]:
    posts = []
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for source in sorted(SOURCE_DIR.glob("*.md")):
        if source.name.startswith("_"):
            continue
        if not VALID_FILENAME.fullmatch(source.name):
            raise ValueError(
                f"Invalid blog filename {source.name!r}. Use letters, numbers, "
                "hyphens, and underscores only; start with a letter or number."
            )
        post = parse_blog_post(source.name, source.read_text(encoding="utf-8"))
        posts.append(post)
    return sorted(posts, key=lambda p: (p["date"], p["title"].casefold()), reverse=True)


def render_markdown(source: str) -> tuple[str, str]:
    try:
        import mistune
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import TextLexer, get_lexer_by_name
    except ImportError as exc:
        raise SystemExit(
            "Blog generation needs its tool dependencies. Install them with:\n"
            "  python -m pip install -r tools/requirements.txt"
        ) from exc

    class PortfolioRenderer(mistune.HTMLRenderer):
        def __init__(self):
            super().__init__(escape=True)
            self.toc_items: list[tuple[int, str, str]] = []
            self._used_ids: set[str] = set()

        def heading(self, text: str, level: int, **attrs) -> str:
            plain = html.unescape(re.sub(r"<[^>]+>", "", text))
            slug = re.sub(r"[^a-z0-9]+", "-", plain.casefold()).strip("-") or "section"
            base_slug = slug
            suffix = 2
            while slug in self._used_ids:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            self._used_ids.add(slug)
            if level >= 2:
                self.toc_items.append((level, slug, plain))
            return f'<h{level} id="{esc(slug)}">{text}</h{level}>\n'

        def block_code(self, code: str, info: str | None = None) -> str:
            language = (info or "").strip().split(maxsplit=1)[0] if info else ""
            try:
                lexer = get_lexer_by_name(language) if language else TextLexer()
            except Exception:
                lexer = TextLexer()
            highlighted = highlight(code, lexer, HtmlFormatter(nowrap=True))
            lang_class = re.sub(r"[^a-zA-Z0-9_-]", "", language)
            class_attr = f' class="language-{esc(lang_class)}"' if lang_class else ""
            return (
                '<div class="codehilite"><pre><code'
                f'{class_attr}>{highlighted}</code></pre></div>\n'
            )

        def render_toc(self) -> str:
            if not self.toc_items:
                return ""
            items = []
            for level, slug, title in self.toc_items:
                indent = " toc-level-3" if level >= 3 else ""
                items.append(
                    f'<li class="{indent.strip()}"><a href="#{esc(slug)}">{esc(title)}</a></li>'
                )
            return '<ul>' + ''.join(items) + '</ul>'

    renderer = PortfolioRenderer()
    markdown = mistune.create_markdown(
        renderer=renderer,
        plugins=["table", "strikethrough", "footnotes"],
    )
    rendered = markdown(source)
    return rendered, renderer.render_toc()


def rewrite_site_asset_paths(rendered_html: str, base_path: str) -> str:
    """Prefix root-relative blog asset references for subfolder deployments."""
    if base_path == "/":
        return rendered_html
    asset_prefix = base_path.rstrip("/") + "/blogs/"
    for attr in ("src", "href"):
        rendered_html = re.sub(
            rf'({attr}=[\"\'])/blogs/',
            lambda match: match.group(1) + asset_prefix,
            rendered_html,
            flags=re.IGNORECASE,
        )
    return rendered_html


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def page_template(*, title: str, description: str, body: str, base_path: str,
                  canonical_url: str = "", og_type: str = "website") -> str:
    canonical = f'<link rel="canonical" href="{esc(canonical_url)}">' if canonical_url else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#070b18">
  <meta name="description" content="{esc(description)}">
  <meta property="og:type" content="{esc(og_type)}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta name="twitter:card" content="summary">
  <title>{esc(title)}</title>
  {canonical}
  <style>{PAGE_CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""


def header_html(base_path: str) -> str:
    return f"""<header class="site-header"><div class="header-inner">
  <a class="brand" href="{esc(base_path)}"><span class="brand-mark">AB.</span>Aissa Bakhil</a>
  <nav class="header-links" aria-label="Main navigation">
    <a href="{esc(base_path)}">Portfolio</a>
    <a href="{esc(base_path + 'blog/')}">Blog</a>
  </nav>
</div></header>"""


def footer_html(base_path: str) -> str:
    return f"""<footer class="site-footer"><span>© {datetime.now().year} Aissa Bakhil</span>
  <a href="{esc(base_path)}">Back to portfolio</a>
</footer>"""


def article_page(post: dict, base_path: str, site_url: str) -> str:
    content_html, toc_html = render_markdown(post["body"])
    content_html = rewrite_site_asset_paths(content_html, base_path)
    tags = "".join(f'<span class="tag">{esc(tag)}</span>' for tag in post["tags"])
    date = esc(post["date"])
    date_html = f'<time datetime="{date}">{date}</time>' if date else ""
    canonical = urljoin(site_url.rstrip("/") + "/", f"blog/{post['slug']}/") if site_url else ""
    toc = f'<aside class="toc"><h2>On this page</h2>{toc_html}</aside>' if toc_html else ""
    lead = f'<p class="lead">{esc(post["description"])}</p>' if post["description"] else ""
    body = f"""{header_html(base_path)}
<main class="page-shell">
  <div class="breadcrumb"><a href="{esc(base_path)}">Home</a> / <a href="{esc(base_path + 'blog/')}">Blog</a> / {esc(post['title'])}</div>
  <header class="article-header">
    <div class="eyebrow">{date_html}<span>·</span><span>{post['reading_time']} min read</span></div>
    <h1>{esc(post['title'])}</h1>
    {lead}
    <div class="tags">{tags}</div>
  </header>
  <div class="article-layout">
    <article class="prose">{content_html}</article>
    {toc}
  </div>
</main>
{footer_html(base_path)}"""
    return page_template(
        title=f"{post['title']} | Aissa Bakhil",
        description=post["description"] or post["title"],
        body=body,
        base_path=base_path,
        canonical_url=canonical,
        og_type="article",
    )


def archive_page(posts: list[dict], base_path: str, site_url: str) -> str:
    cards = []
    for post in posts:
        meta = []
        if post["date"]:
            meta.append(f'<time>{esc(post["date"])}</time>')
        meta.append(f'<span>{post["reading_time"]} min read</span>')
        tag_html = "".join(f'<span class="tag">{esc(tag)}</span>' for tag in post["tags"])
        cards.append(
            f'<a class="post-card" href="{esc(base_path + "blog/" + post["slug"] + "/")}">'
            f'<div class="post-meta">{"<span>·</span>".join(meta)}</div>'
            f'<h2>{esc(post["title"])}</h2>'
            f'<p>{esc(post["description"] or "Read the article.")}</p>'
            f'<div class="tags">{tag_html}</div>'
            '<span class="read-link">Read article →</span></a>'
        )
    listing = "".join(cards) if cards else (
        '<div class="empty-state">No articles have been published yet. Please check back soon.</div>'
    )
    body = f"""{header_html(base_path)}
<main class="page-shell">
  <header class="archive-heading"><h1>Writing &amp; notes</h1>
    <p>Articles, technical notes, and lessons from building software and intelligent systems.</p>
  </header>
  <section class="post-list" aria-label="Published articles">{listing}</section>
</main>
{footer_html(base_path)}"""
    canonical = urljoin(site_url.rstrip("/") + "/", "blog/") if site_url else ""
    return page_template(
        title="Blog | Aissa Bakhil",
        description="Articles, technical notes, and lessons from building software and intelligent systems.",
        body=body,
        base_path=base_path,
        canonical_url=canonical,
    )


def write_manifest(posts: list[dict]) -> None:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    data = [public_post_metadata(post) for post in posts]
    MANIFEST_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean_stale_pages(current_slugs: set[str]) -> None:
    """Remove only old generated post folders recorded in the previous manifest."""
    if not MANIFEST_PATH.exists():
        return
    try:
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for entry in previous if isinstance(previous, list) else []:
        slug = entry.get("slug") if isinstance(entry, dict) else None
        if not isinstance(slug, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", slug):
            continue
        if slug not in current_slugs:
            stale = BLOG_ASSETS_DIR / slug
            if stale.is_dir():
                shutil.rmtree(stale)


def build(base_path: str, site_url: str) -> int:
    posts = read_posts()
    BLOG_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    clean_stale_pages({post["slug"] for post in posts})

    for post in posts:
        output_dir = BLOG_ASSETS_DIR / post["slug"]
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text(
            article_page(post, base_path, site_url), encoding="utf-8"
        )

    archive_path = BLOG_ASSETS_DIR / "index.html"
    archive_path.write_text(archive_page(posts, base_path, site_url), encoding="utf-8")
    write_manifest(posts)

    # Optional sitemap generation: canonical URLs are only emitted when the
    # owner provides the real production domain through --site-url or SITE_URL.
    sitemap_path = ASSETS_DIR / "blog-sitemap.xml"
    if site_url:
        urls = [urljoin(site_url.rstrip("/") + "/", "blog/")]
        urls.extend(urljoin(site_url.rstrip("/") + "/", f"blog/{p['slug']}/") for p in posts)
        sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        sitemap += "".join(f"<url><loc>{html.escape(url)}</loc></url>" for url in urls)
        sitemap += "</urlset>\n"
        sitemap_path.write_text(sitemap, encoding="utf-8")
    elif sitemap_path.exists():
        sitemap_path.unlink()

    print(f"Generated {len(posts)} blog article page(s) in {BLOG_ASSETS_DIR}")
    print(f"Generated archive: {archive_path}")
    print(f"Generated Flet index: {MANIFEST_PATH}")
    return len(posts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-path", default=os.getenv("BASE_PATH", "/"),
        help="Public site base path, e.g. /portfolio/ (default: /).",
    )
    parser.add_argument(
        "--site-url", default=os.getenv("SITE_URL", "").strip(),
        help="Canonical production origin, e.g. https://example.com (optional).",
    )
    args = parser.parse_args()
    base_path = normalize_base_path(args.base_path)
    site_url = args.site_url.strip().rstrip("/")
    if site_url and not re.match(r"^https?://", site_url, re.IGNORECASE):
        parser.error("--site-url must start with https:// or http://")
    build(base_path, site_url)


if __name__ == "__main__":
    main()
