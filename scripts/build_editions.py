#!/usr/bin/env python3
"""Assemble manuscript editions into exportable Markdown and HTML files."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
BOOK_PATH = ROOT / "book.yml"
EXPORTS_DIR = ROOT / "exports"
REVIEW_REF_RE = re.compile(r'<span class="review-ref">\[(.*?)\]</span>')


def load_book() -> dict:
    return yaml.safe_load(BOOK_PATH.read_text(encoding="utf-8"))


def read_manifest(manifest_path: Path) -> list[Path]:
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    return [ROOT / line.strip() for line in lines if line.strip()]


def assemble_markdown(paths: list[Path], include_review_references: bool) -> str:
    chunks: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8").strip()
        if not include_review_references:
            text = REVIEW_REF_RE.sub("", text)
            text = re.sub(r" +\n", "\n", text)
        chunks.append(text)
    return "\n\n".join(chunks).strip() + "\n"


def markdown_to_html(markdown_text: str, title: str, stylesheets: list[str]) -> str:
    html_lines: list[str] = []
    in_paragraph = False

    def close_paragraph() -> None:
        nonlocal in_paragraph
        if in_paragraph:
            html_lines.append("</p>")
            in_paragraph = False

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            close_paragraph()
            continue

        if line.startswith("### "):
            close_paragraph()
            html_lines.append(f"<h3>{html.escape(line[4:])}</h3>")
            continue
        if line.startswith("## "):
            close_paragraph()
            html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            continue
        if line.startswith("# "):
            close_paragraph()
            html_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
            continue

        escaped = html.escape(line, quote=False)
        escaped = escaped.replace("&lt;span class=\"review-ref\"&gt;", '<span class="review-ref">')
        escaped = escaped.replace("&lt;/span&gt;", "</span>")

        if not in_paragraph:
            html_lines.append("<p>")
            in_paragraph = True
        else:
            html_lines.append("<br>")
        html_lines.append(escaped)

    close_paragraph()

    style_tags = "\n".join(
        f'  <link rel="stylesheet" href="../{html.escape(stylesheet)}">' for stylesheet in stylesheets
    )

    body = "\n".join(f"  {line}" for line in html_lines)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        f"  <title>{html.escape(title)}</title>\n"
        f"{style_tags}\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def slug_for_edition(name: str) -> str:
    return name.replace("_pdf", "")


def build_editions(selected: list[str] | None = None) -> list[Path]:
    book = load_book()
    project = book["project"]
    edition_defaults = book.get("edition_defaults", {})
    editions = book["editions"]
    built_paths: list[Path] = []

    EXPORTS_DIR.mkdir(exist_ok=True)

    for name, config in editions.items():
        if selected and name not in selected:
            continue

        manifest = ROOT / config["manifest"]
        include_review_references = config.get(
            "include_review_references",
            edition_defaults.get("include_review_references", False),
        )
        stylesheets = config.get("stylesheets", [])
        title = project["title"]
        if "subtitle" in project:
            title = f"{title}: {project['subtitle']}"

        markdown_text = assemble_markdown(read_manifest(manifest), include_review_references)
        slug = slug_for_edition(name)
        md_path = EXPORTS_DIR / f"{slug}.md"
        html_path = EXPORTS_DIR / f"{slug}.html"

        md_path.write_text(markdown_text, encoding="utf-8")
        html_path.write_text(markdown_to_html(markdown_text, title, stylesheets), encoding="utf-8")

        built_paths.extend([md_path, html_path])

    return built_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--edition",
        action="append",
        choices=["review_pdf", "reader_pdf", "epub", "pod_print"],
        help="Build only the selected edition(s).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    built_paths = build_editions(args.edition)
    if not built_paths:
        print("No editions were built.")
        return 1

    print("Built exports:")
    for path in built_paths:
        print(f"- {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
