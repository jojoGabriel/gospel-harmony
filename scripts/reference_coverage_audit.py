#!/usr/bin/env python3
"""Audit Gospel reference coverage from the section mapping in references.md."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REFERENCES_PATH = ROOT / "references.md"
EXPORT_PATH = ROOT / "exports" / "reference_coverage.md"

CHAPTER_VERSE_COUNTS = {
    "Matthew": [25, 23, 17, 25, 48, 34, 29, 34, 38, 42, 30, 50, 58, 36, 39, 28, 27, 35, 30, 34, 46, 46, 39, 51, 46, 75, 66, 20],
    "Mark": [45, 28, 35, 41, 43, 56, 37, 38, 50, 52, 33, 44, 37, 72, 47, 20],
    "Luke": [80, 52, 38, 44, 39, 49, 50, 56, 62, 42, 54, 59, 35, 35, 32, 31, 37, 43, 48, 47, 38, 71, 56, 53],
    "John": [51, 25, 36, 54, 47, 71, 53, 59, 41, 42, 57, 50, 38, 31, 27, 33, 26, 40, 42, 31, 25],
}

GOSPELS = ["Matthew", "Mark", "Luke", "John"]
SECTION_HEADER_RE = re.compile(r"^### (.+)$")
BOOK_LINE_RE = re.compile(r"^- (Matthew|Mark|Luke|John): (.+)$")


def parse_references() -> dict[str, list[tuple[str, str]]]:
    references_text = REFERENCES_PATH.read_text(encoding="utf-8")
    mapping: dict[str, list[tuple[str, str]]] = defaultdict(list)
    current_section = ""

    for line in references_text.splitlines():
        header_match = SECTION_HEADER_RE.match(line)
        if header_match:
            current_section = header_match.group(1)
            continue

        book_match = BOOK_LINE_RE.match(line)
        if not book_match:
            continue

        gospel, value = book_match.groups()
        if value.strip() == "none":
            continue

        for part in value.split(";"):
            part = part.strip()
            if part:
                mapping[gospel].append((current_section, part))

    return mapping


def parse_range_part(part: str) -> list[tuple[int, int, int, int]]:
    ranges: list[tuple[int, int, int, int]] = []
    current_chapter: int | None = None

    for segment in [piece.strip() for piece in part.split(",")]:
        if not segment:
            continue

        if "-" in segment:
            start_text, end_text = [piece.strip() for piece in segment.split("-", 1)]

            if ":" in start_text:
                start_chapter, start_verse = map(int, start_text.split(":", 1))
            else:
                if current_chapter is None:
                    raise ValueError(f"Cannot infer chapter for segment {segment!r}")
                start_chapter, start_verse = current_chapter, int(start_text)

            if ":" in end_text:
                end_chapter, end_verse = map(int, end_text.split(":", 1))
            else:
                end_chapter, end_verse = start_chapter, int(end_text)

            current_chapter = end_chapter
            ranges.append((start_chapter, start_verse, end_chapter, end_verse))
            continue

        if ":" not in segment:
            raise ValueError(f"Unsupported reference segment {segment!r}")

        chapter, verse = map(int, segment.split(":", 1))
        current_chapter = chapter
        ranges.append((chapter, verse, chapter, verse))

    return ranges


def build_coverage(mapping: dict[str, list[tuple[str, str]]]) -> tuple[dict[str, dict[int, set[int]]], dict[str, list[tuple[str, int, int, int, int]]]]:
    coverage: dict[str, dict[int, set[int]]] = defaultdict(lambda: defaultdict(set))
    expanded: dict[str, list[tuple[str, int, int, int, int]]] = defaultdict(list)

    for gospel, entries in mapping.items():
        chapter_counts = CHAPTER_VERSE_COUNTS[gospel]
        for section, part in entries:
            for start_ch, start_vs, end_ch, end_vs in parse_range_part(part):
                expanded[gospel].append((section, start_ch, start_vs, end_ch, end_vs))
                for chapter in range(start_ch, end_ch + 1):
                    from_verse = start_vs if chapter == start_ch else 1
                    to_verse = end_vs if chapter == end_ch else chapter_counts[chapter - 1]
                    coverage[gospel][chapter].update(range(from_verse, to_verse + 1))

    return coverage, expanded


def format_range(chapter: int, start_verse: int, end_verse: int) -> str:
    if start_verse == end_verse:
        return f"{chapter}:{start_verse}"
    return f"{chapter}:{start_verse}-{end_verse}"


def missing_ranges(gospel: str, coverage: dict[int, set[int]]) -> list[str]:
    results: list[str] = []
    for chapter, last_verse in enumerate(CHAPTER_VERSE_COUNTS[gospel], start=1):
        present = coverage.get(chapter, set())
        start = None
        for verse in range(1, last_verse + 1):
            if verse not in present and start is None:
                start = verse
            elif verse in present and start is not None:
                results.append(format_range(chapter, start, verse - 1))
                start = None
        if start is not None:
            results.append(format_range(chapter, start, last_verse))
    return results


def covered_ranges(gospel: str, coverage: dict[int, set[int]]) -> list[str]:
    results: list[str] = []
    for chapter, last_verse in enumerate(CHAPTER_VERSE_COUNTS[gospel], start=1):
        present = coverage.get(chapter, set())
        if not present:
            continue
        start = None
        for verse in range(1, last_verse + 1):
            if verse in present and start is None:
                start = verse
            elif verse not in present and start is not None:
                results.append(format_range(chapter, start, verse - 1))
                start = None
        if start is not None:
            results.append(format_range(chapter, start, last_verse))
    return results


def build_report() -> str:
    mapping = parse_references()
    coverage, _ = build_coverage(mapping)

    lines = [
        "# Gospel Reference Coverage Audit",
        "",
        "This report audits the section-level Gospel ranges recorded in `references.md`.",
        "It shows what the manuscript currently covers when all section ranges are combined,",
        "and it identifies the remaining chapter-and-verse gaps in Matthew, Mark, Luke, and John.",
        "",
    ]

    for gospel in GOSPELS:
        chapter_total = sum(CHAPTER_VERSE_COUNTS[gospel])
        covered = sum(len(coverage[gospel].get(chapter, set())) for chapter in range(1, len(CHAPTER_VERSE_COUNTS[gospel]) + 1))
        percent = (covered / chapter_total) * 100
        present = covered_ranges(gospel, coverage[gospel])
        missing = missing_ranges(gospel, coverage[gospel])

        lines.extend(
            [
                f"## {gospel}",
                "",
                f"- Covered verses: {covered} / {chapter_total} ({percent:.1f}%)",
                f"- Covered ranges: {'; '.join(present) if present else 'none'}",
                f"- Missing ranges: {'; '.join(missing) if missing else 'none'}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    EXPORT_PATH.parent.mkdir(exist_ok=True)
    report = build_report()
    EXPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote {EXPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
