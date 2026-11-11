# Aissa Bakhil — AI/ML Engineering Portfolio

A responsive Flet portfolio with a Markdown-powered blog. The Flet application renders the portfolio and article summaries; each full article is generated as a standalone static HTML page.

## Project structure

```text
.
├── main.py                    # Flet portfolio
├── blog_utils.py              # Shared Markdown metadata parsing
├── requirements.txt           # Runtime dependency for the portfolio
├── blogs/                     # Markdown source files (source of truth)
│   └── _template.md
├── tools/
│   ├── build_blogs.py          # Generates static article pages + index
│   ├── sync_blogs.py           # Backward-compatible alias
│   └── requirements.txt        # Build-time Markdown/highlighting tools
└── assets/
    ├── hero.png
    ├── profile.jpeg           # Profile photo
    ├── blogs/
    │   ├── index.json         # Generated summary manifest used by Flet
    │   └── images/            # Put images used by articles here
    └── blog/
        ├── index.html         # Generated static blog archive
        └── <slug>/index.html  # Generated standalone article pages
```

## Install

```bash
python -m pip install -r requirements.txt
python -m pip install -r tools/requirements.txt
```

The second command installs build-time tools only; they are not needed to run the published website.

## Write a blog post

Create a Markdown file in `blogs/`, for example `blogs/understanding-rag.md`:

````markdown
---
title: "Understanding retrieval-augmented generation"
date: 2026-11-11
description: "A practical overview of retrieval, context construction, and evaluation."
tags: AI, Python, Information Retrieval
---

## Introduction

Write your article using Markdown.

## A code example

```python
def retrieve(query: str) -> list[str]:
    return []
```

## A table

| Component | Responsibility |
|---|---|
| Retriever | Finds relevant passages |
| Generator | Produces a grounded answer |
````

Front matter is optional. Supported fields are `title`, `date` (`YYYY-MM-DD`), `description`, and comma-separated `tags`. Without a title, the first H1 or filename is used. Files beginning with `_` are treated as templates and ignored.

For article images, place files in `assets/blogs/images/` and reference them from Markdown using a root-relative path:

```markdown
![Retrieval architecture](/blogs/images/retrieval-architecture.png)
```

The builder supports headings, links, lists, blockquotes, tables, fenced code blocks with syntax highlighting, strikethrough, and footnotes. It escapes raw HTML in Markdown for safer static output.

## Preview locally

Generate the static pages first, then start Flet:

```bash
python tools/build_blogs.py
flet run --web main.py
```

The portfolio's Blog section links directly to `/blog/<slug>/`. The complete archive is available at `/blog/`.

## Build the static website

```bash
python tools/build_blogs.py
flet build web
```

Flet copies the contents of `assets/` into the web build output. The generated pages therefore appear as `build/web/blog/index.html` and `build/web/blog/<slug>/index.html` next to the Flet app's `index.html`.

You can preview the built site with:

```bash
flet serve
```

Then open the local address printed by Flet. Alternatively, serve the `build/web` directory with a static file server.

### Hosting below a subdirectory

If the site is hosted at `https://example.com/portfolio/`, use the same base path for both commands:

```bash
python tools/build_blogs.py --base-path /portfolio/ --site-url https://example.com/portfolio/
flet build web --base-url /portfolio/
```

`--site-url` is optional; provide your actual public URL to add canonical links and generate `assets/blog-sitemap.xml`. Do not use an example domain in production.

## How it works

1. You write and maintain posts in `blogs/*.md`.
2. `tools/build_blogs.py` reads metadata and converts each post to an independent HTML document.
3. The script writes the blog archive to `assets/blog/index.html` and a small JSON summary manifest to `assets/blogs/index.json`.
4. The Flet homepage loads only the summary manifest. Clicking an article opens its static HTML page; the Flet app does not need to render the full Markdown content.
5. `flet build web` copies the generated HTML and image assets into the final static website.

No database, CMS, API server, or runtime Markdown rendering is required.
