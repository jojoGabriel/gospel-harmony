import unittest
from pathlib import Path
import tempfile

from scripts import manuscript_lint


class ParseParagraphsTests(unittest.TestCase):
    def test_flags_narrative_line_without_review_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.md"
            path.write_text(
                "# Sample\n\nReferences: Test\n\nThis line has no review ref.\n",
                encoding="utf-8",
            )

            paragraphs, errors = manuscript_lint.parse_paragraphs(path)

        self.assertEqual(paragraphs, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("missing a review reference", errors[0])


class AnchorLintTests(unittest.TestCase):
    def test_reports_missing_required_anchor_terms(self) -> None:
        paragraph = manuscript_lint.Paragraph(
            file_path=manuscript_lint.ROOT / "sections" / "02_john_baptist_ministry.md",
            line_number=23,
            text="When the wine was gone, His mother said to Him, \"They have no wine.\"",
            refs_raw="John 2:1-11",
        )
        checks = {
            "required_anchor_checks": [
                {
                    "id": "cana-dialogue",
                    "ref": "John 2:1-11",
                    "all_of": ["woman", "hour"],
                    "explanation": "Example check",
                }
            ]
        }

        errors = manuscript_lint.lint([paragraph], checks)

        self.assertEqual(len(errors), 1)
        self.assertIn("missing shared-core anchors", errors[0])
        self.assertIn("woman", errors[0])
        self.assertIn("hour", errors[0])

    def test_quote_sensitive_check_requires_multiple_quote_spans(self) -> None:
        paragraph = manuscript_lint.Paragraph(
            file_path=manuscript_lint.ROOT / "sections" / "03_galilean_ministry.md",
            line_number=17,
            text="He read from Isaiah and then said, \"Today this Scripture has been fulfilled.\"",
            refs_raw="Luke 4:16-21",
        )
        checks = {
            "required_anchor_checks": [
                {
                    "id": "nazareth-isaiah-quote",
                    "ref": "Luke 4:16-21",
                    "all_of": ["today this scripture has been fulfilled"],
                    "min_quote_spans": 2,
                    "explanation": "Example check",
                }
            ]
        }

        errors = manuscript_lint.lint([paragraph], checks)

        self.assertEqual(len(errors), 1)
        self.assertIn("expected at least 2 quoted span(s)", errors[0])

    def test_multi_gospel_schema_allows_partial_distinctives_without_overfitting(self) -> None:
        paragraph = manuscript_lint.Paragraph(
            file_path=manuscript_lint.ROOT / "sections" / "05_final_journey.md",
            line_number=33,
            text=(
                'They cried out, "Hosanna!" and said, "Blessed is the King who comes in the name '
                'of the Lord." Jesus answered that if they became silent, the stones would cry out.'
            ),
            refs_raw="Matt 21:1-11; Mark 11:1-10; Luke 19:28-40; John 12:12-19",
        )
        checks = {
            "required_anchor_checks": [
                {
                    "id": "triumphal-entry",
                    "ref": "Matt 21:1-11",
                    "shared_core": ["hosanna"],
                    "distinctive_details": {
                        "items": [
                            "stones themselves would cry out",
                            {"label": "king acclamation", "any_of": ["king who comes", "king of israel"]},
                        ],
                        "min_present": 1,
                    },
                    "explanation": "Example check",
                }
            ]
        }

        errors = manuscript_lint.lint([paragraph], checks)

        self.assertEqual(errors, [])

    def test_multi_gospel_schema_fails_when_too_many_distinctives_are_missing(self) -> None:
        paragraph = manuscript_lint.Paragraph(
            file_path=manuscript_lint.ROOT / "sections" / "05_final_journey.md",
            line_number=33,
            text='They cried out, "Hosanna!" as He entered the city.',
            refs_raw="Matt 21:1-11; Mark 11:1-10; Luke 19:28-40; John 12:12-19",
        )
        checks = {
            "required_anchor_checks": [
                {
                    "id": "triumphal-entry",
                    "ref": "Matt 21:1-11",
                    "shared_core": ["hosanna"],
                    "distinctive_details": {
                        "items": ["stones themselves would cry out", "king who comes in the name of the lord"],
                        "min_present": 1,
                    },
                    "explanation": "Example check",
                }
            ]
        }

        errors = manuscript_lint.lint([paragraph], checks)

        self.assertEqual(len(errors), 1)
        self.assertIn("distinctive anchor", errors[0])

    def test_repo_checks_pass_on_current_sections(self) -> None:
        checks = manuscript_lint.load_checks()
        all_paragraphs = []
        all_errors = []

        for path in manuscript_lint.iter_section_files():
            paragraphs, errors = manuscript_lint.parse_paragraphs(path)
            all_paragraphs.extend(paragraphs)
            all_errors.extend(errors)

        all_errors.extend(manuscript_lint.lint(all_paragraphs, checks))

        self.assertEqual(all_errors, [])

    def test_uncovered_paragraphs_reports_missing_coverage(self) -> None:
        paragraph = manuscript_lint.Paragraph(
            file_path=manuscript_lint.ROOT / "sections" / "00_prologue.md",
            line_number=7,
            text="There was a man sent from God, whose name was John.",
            refs_raw="John 1:6-8",
        )
        checks = {"required_anchor_checks": []}

        uncovered = manuscript_lint.uncovered_paragraphs([paragraph], checks)
        report = manuscript_lint.format_coverage_report([paragraph], checks)

        self.assertEqual(uncovered, [paragraph])
        self.assertIn("Uncovered: 1", report)
        self.assertIn("00_prologue.md:7 [John 1:6-8]", report)


if __name__ == "__main__":
    unittest.main()
