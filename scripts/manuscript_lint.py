#!/usr/bin/env python3
"""Lint the harmonized manuscript for structural and curated content checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
SECTIONS_DIR = ROOT / "sections"
CHECKS_PATH = ROOT / "manifests" / "manuscript_checks.json"
REVIEW_REF_RE = re.compile(r'<span class="review-ref">\[(.*?)\]</span>')
QUOTE_SPAN_RE = re.compile(r'"([^"]+)"')


@dataclass
class Paragraph:
    file_path: Path
    line_number: int
    text: str
    refs_raw: str


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_checks(checks_path: Path = CHECKS_PATH) -> dict:
    return json.loads(checks_path.read_text(encoding="utf-8"))


def iter_section_files(sections_dir: Path = SECTIONS_DIR) -> Iterable[Path]:
    return sorted(sections_dir.glob("*.md"))


def parse_paragraphs(path: Path) -> tuple[list[Paragraph], list[str]]:
    paragraphs: list[Paragraph] = []
    structural_errors: list[str] = []

    lines = path.read_text(encoding="utf-8").splitlines()
    current_block: list[str] = []
    block_start_line = 1

    def flush_block() -> None:
        nonlocal current_block, block_start_line
        if not current_block:
            return

        block_text = "\n".join(current_block).strip()
        current_block = []
        if not block_text or block_text.startswith("#") or block_text.startswith("References:"):
            return

        match = REVIEW_REF_RE.search(block_text)
        if not match:
            structural_errors.append(
                f"{display_path(path)}:{block_start_line}: narrative paragraph is missing a review reference"
            )
            return

        text = REVIEW_REF_RE.sub("", block_text).strip()
        paragraphs.append(
            Paragraph(
                file_path=path,
                line_number=block_start_line,
                text=text,
                refs_raw=match.group(1),
            )
        )

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line:
            continue

        if not current_block and (line.startswith("#") or line.startswith("References:")):
            continue

        if not current_block:
            block_start_line = line_number

        current_block.append(line)

        if REVIEW_REF_RE.search(line):
            flush_block()

    flush_block()

    return paragraphs, structural_errors


def find_paragraphs_by_ref(paragraphs: Iterable[Paragraph], ref: str) -> list[Paragraph]:
    ref_lower = ref.lower()
    return [paragraph for paragraph in paragraphs if ref_lower in paragraph.refs_raw.lower()]


def quote_span_count(text: str) -> int:
    return len(QUOTE_SPAN_RE.findall(text))


def anchor_label(anchor: str | dict) -> str:
    if isinstance(anchor, str):
        return anchor
    if "label" in anchor:
        return str(anchor["label"])
    if "any_of" in anchor:
        return " / ".join(anchor["any_of"])
    return str(anchor)


def anchor_matches(text: str, anchor: str | dict) -> bool:
    if isinstance(anchor, str):
        return anchor.lower() in text
    if "any_of" in anchor:
        return any(option.lower() in text for option in anchor["any_of"])
    return False


def missing_anchors(text: str, anchors: list[str | dict]) -> list[str]:
    return [anchor_label(anchor) for anchor in anchors if not anchor_matches(text, anchor)]


def count_present_anchors(text: str, anchors: list[str | dict]) -> int:
    return sum(1 for anchor in anchors if anchor_matches(text, anchor))


def matching_checks_for_paragraph(paragraph: Paragraph, checks: dict) -> list[dict]:
    refs_lower = paragraph.refs_raw.lower()
    return [
        check for check in checks.get("required_anchor_checks", []) if check["ref"].lower() in refs_lower
    ]


def uncovered_paragraphs(paragraphs: Iterable[Paragraph], checks: dict) -> list[Paragraph]:
    return [paragraph for paragraph in paragraphs if not matching_checks_for_paragraph(paragraph, checks)]


def format_coverage_report(paragraphs: list[Paragraph], checks: dict) -> str:
    uncovered = uncovered_paragraphs(paragraphs, checks)
    covered_count = len(paragraphs) - len(uncovered)
    section_counts = Counter(paragraph.file_path.name for paragraph in uncovered)

    lines = [
        "Coverage report:",
        f"- Paragraphs: {len(paragraphs)}",
        f"- Covered by at least one content check: {covered_count}",
        f"- Uncovered: {len(uncovered)}",
    ]

    if uncovered:
        lines.append("- Uncovered by section:")
        for section_name, count in sorted(section_counts.items()):
            lines.append(f"  - {section_name}: {count}")

        lines.append("- Uncovered paragraphs:")
        for paragraph in uncovered:
            lines.append(
                f"  - {display_path(paragraph.file_path)}:{paragraph.line_number} [{paragraph.refs_raw}]"
            )

    return "\n".join(lines)


def lint(paragraphs: list[Paragraph], checks: dict) -> list[str]:
    errors: list[str] = []

    for check in checks.get("required_anchor_checks", []):
        matched = find_paragraphs_by_ref(paragraphs, check["ref"])
        if not matched:
            errors.append(f"Missing paragraph for configured reference {check['ref']} ({check['id']})")
            continue

        text_blob = "\n".join(paragraph.text.lower() for paragraph in matched)
        shared_core = check.get("shared_core", check.get("all_of", []))
        missing_terms = missing_anchors(text_blob, shared_core)
        if missing_terms:
            locations = ", ".join(
                f"{display_path(paragraph.file_path)}:{paragraph.line_number}" for paragraph in matched
            )
            errors.append(
                f"{check['id']} failed at {locations}: missing shared-core anchors {missing_terms}. "
                f"{check.get('explanation', '')}".strip()
            )

        distinctive_details = check.get("distinctive_details")
        if distinctive_details:
            distinctives = distinctive_details.get("items", [])
            min_present = distinctive_details.get("min_present", 1)
            present_count = count_present_anchors(text_blob, distinctives)
            if present_count < min_present:
                locations = ", ".join(
                    f"{display_path(paragraph.file_path)}:{paragraph.line_number}" for paragraph in matched
                )
                errors.append(
                    f"{check['id']} failed at {locations}: expected at least {min_present} distinctive "
                    f"anchor(s), found {present_count}. Options were "
                    f"{[anchor_label(anchor) for anchor in distinctives]}. "
                    f"{check.get('explanation', '')}".strip()
                )

        quotation_anchors = check.get("quotation_anchors")
        if quotation_anchors:
            quote_items = quotation_anchors.get("items", [])
            min_present = quotation_anchors.get("min_present", len(quote_items))
            present_count = count_present_anchors(text_blob, quote_items)
            if present_count < min_present:
                locations = ", ".join(
                    f"{display_path(paragraph.file_path)}:{paragraph.line_number}" for paragraph in matched
                )
                errors.append(
                    f"{check['id']} failed at {locations}: expected at least {min_present} quotation "
                    f"anchor(s), found {present_count}. Options were "
                    f"{[anchor_label(anchor) for anchor in quote_items]}. "
                    f"{check.get('explanation', '')}".strip()
                )

        min_quote_spans = check.get("min_quote_spans")
        if min_quote_spans is not None:
            actual_quote_spans = sum(quote_span_count(paragraph.text) for paragraph in matched)
            if actual_quote_spans < min_quote_spans:
                locations = ", ".join(
                    f"{display_path(paragraph.file_path)}:{paragraph.line_number}" for paragraph in matched
                )
                errors.append(
                    f"{check['id']} failed at {locations}: expected at least {min_quote_spans} quoted span(s), "
                    f"found {actual_quote_spans}. {check.get('explanation', '')}".strip()
                )

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report-coverage",
        action="store_true",
        help="Print paragraph-by-paragraph content-check coverage information.",
    )
    parser.add_argument(
        "--fail-on-uncovered",
        action="store_true",
        help="Treat paragraphs without any content check as a failure.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    checks = load_checks()
    all_paragraphs: list[Paragraph] = []
    errors: list[str] = []

    for path in iter_section_files():
        paragraphs, structural_errors = parse_paragraphs(path)
        all_paragraphs.extend(paragraphs)
        errors.extend(structural_errors)

    errors.extend(lint(all_paragraphs, checks))

    uncovered = uncovered_paragraphs(all_paragraphs, checks)
    if args.fail_on_uncovered and uncovered:
        errors.append(f"{len(uncovered)} paragraph(s) are still uncovered by content checks.")

    if errors:
        print("Manuscript lint failed:")
        for error in errors:
            print(f"- {error}")
        if args.report_coverage:
            print()
            print(format_coverage_report(all_paragraphs, checks))
        return 1

    print(
        f"Manuscript lint passed for {len(all_paragraphs)} paragraph(s) across "
        f"{len(list(iter_section_files()))} section file(s)."
    )
    if args.report_coverage:
        print()
        print(format_coverage_report(all_paragraphs, checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
