"""Shared Markdown metadata helpers used by the Flet app and blog builder."""
from __future__ import annotations

import csv
import math
import re
from pathlib import Path

SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_tags(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    try:
        values = next(csv.reader([value], skipinitialspace=True)) if value else []
    except csv.Error:
        values = value.split(",")
    return [_unquote(tag).strip() for tag in values if _unquote(tag).strip()]


def split_front_matter(raw: str) -> tuple[dict, str]:
    """Parse the project's intentionally small YAML-like front matter format."""
    text = raw.lstrip("\ufeff")
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return {}, text

    lines = text.splitlines()
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        return {}, text

    metadata: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "tags":
            metadata[key] = _parse_tags(value)
        else:
            metadata[key] = _unquote(value)

    return metadata, "\n".join(lines[closing + 1:]).lstrip()


def _plain_text(markdown_text: str) -> str:
    text = re.sub(r"```.*?```", " ", markdown_text, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", " ", text, flags=re.DOTALL)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[#>*_~|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_description(body: str, limit: int = 190) -> str:
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph or paragraph.startswith(("#", "```", "~~~", "|", "- ", "* ")):
            continue
        description = _plain_text(paragraph)
        if description:
            if len(description) > limit:
                return description[: limit - 3].rsplit(" ", 1)[0] + "..."
            return description
    return ""


def parse_blog_post(filename: str, raw: str) -> dict:
    """Return normalized metadata and Markdown content for one post."""
    file_path = Path(filename)
    slug = file_path.stem
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError(
            f"Invalid blog filename {file_path.name!r}; use letters, numbers, "
            "hyphens, and underscores only, with a letter or number first."
        )

    metadata, body = split_front_matter(raw)
    title = str(metadata.get("title", "")).strip()
    if not title:
        heading = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
        title = heading.group(1).strip() if heading else slug.replace("-", " ").replace("_", " ").title()

    # The generated article page owns the H1, so remove a duplicate leading H1.
    first_heading = re.match(r"^#\s+(.+)\s*(?:\n|$)", body)
    if first_heading and first_heading.group(1).strip().casefold() == title.casefold():
        body = body[first_heading.end():].lstrip()

    description = str(metadata.get("description", "")).strip() or _extract_description(body)
    raw_tags = metadata.get("tags", [])
    tags = raw_tags if isinstance(raw_tags, list) else _parse_tags(str(raw_tags))
    tags = [str(tag).strip() for tag in tags if str(tag).strip()]
    date = str(metadata.get("date", "")).strip()

    words = len(re.findall(r"\b[\w'-]+\b", _plain_text(body)))
    reading_time = max(1, math.ceil(words / 220))

    return {
        "slug": slug,
        "filename": file_path.name,
        "title": title,
        "date": date,
        "description": description,
        "tags": tags,
        "reading_time": reading_time,
        "body": body,
    }


def public_post_metadata(post: dict) -> dict:
    """Fields needed by the Flet blog index; Markdown stays in the source file."""
    return {
        "slug": post["slug"],
        "title": post["title"],
        "date": post["date"],
        "description": post["description"],
        "tags": post["tags"],
        "reading_time": post["reading_time"],
        "url": f"blog/{post['slug']}/",
    }
