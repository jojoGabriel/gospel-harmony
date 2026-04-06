# One Jesus, Out of Four

This project develops a single, condensed Gospel narrative by harmonizing Matthew, Mark, Luke, and John into one continuous account.

## Objective

Create a coherent, readable, and faithful harmonized Gospel that:

- Reads like one continuous book
- Preserves the intent of Scripture
- Balances clarity with accuracy

## Core Requirements

- Arrange events in chronological order
- Organize the narrative into clear sections
- Include section titles and reference citations
- Write in readable but not modernized English
- Condense repetition across parallel accounts
- Merge overlapping passages smoothly
- Maintain a single-author voice
- Avoid contradictions and duplicate storytelling
- Use pure prose with no verse numbers in the body text

## Purpose And Limits

This project seeks to produce a readable and faithful harmonized narrative of Matthew, Mark, Luke, and John in one continuous account.

Even where it aims to stay very close to the wording and meaning of Scripture, it is not itself Scripture, it is not a Bible translation, and it is not meant to replace the Bible. The Bible remains the primary and authoritative text, and this work is a secondary tool for reading, comparison, and study.

## Project Structure

```text
front_matter/
  01_title.md
  02_copyright.md
  03_purpose_limits.md
  04_preface.md
sections/
  00_prologue.md
  01_birth_early_years.md
  02_john_baptist_ministry.md
  03_galilean_ministry.md
  04_teachings_parables.md
  05_final_journey.md
  06_crucifixion.md
  07_resurrection.md
back_matter/
  01_note_on_method.md
  02_note_on_sources.md
manifests/
  review.txt
  reader.txt
styles/
  base.css
  print.css
  epub.css
  review.css
  reader.css
publishing/
  README.md
assets/cover/
exports/
book.yml
style_guide.md
references.md
prompt_template.md
```

## Workflow

1. Gather all relevant passages for a section.
2. Merge overlapping accounts.
3. Place non-chronological theological material, such as John's opening prologue, ahead of the historical narrative where appropriate.
4. Produce one smooth narrative in a unified voice.
5. Revise for clarity, theological accuracy, and flow.

## Automated Checks

Run the manuscript lint pass with:

```bash
python3 scripts/manuscript_lint.py
```

See paragraph-by-paragraph content-check coverage with:

```bash
python3 scripts/manuscript_lint.py --report-coverage
```

When the curated suite is mature enough to enforce full paragraph coverage, use:

```bash
python3 scripts/manuscript_lint.py --report-coverage --fail-on-uncovered
```

This check currently does two things:

- verifies that narrative paragraphs in `sections/` still carry review references
- enforces curated anchor checks for passages where a key phrase or quotation is easy to lose during revision

The anchor rules live in `manifests/manuscript_checks.json`, so additional cases can be added over time as the team finds fragile passages worth guarding. Coverage reporting makes it possible to see which paragraph blocks still have no content-level check at all.

For multi-Gospel passages, prefer this schema in each rule:

- `shared_core`: anchors the harmony should always preserve from the combined witness
- `distinctive_details`: optional details that should survive from one or more parallel accounts, with `min_present` to avoid overfitting
- `quotation_anchors`: key sayings or quotation-shaped phrases, also with `min_present` when multiple faithful forms are acceptable

Keep anchors short and meaning-bearing. The goal is to guard indispensable content from trusted translation traditions without forcing one exact English wording.

## Publishing Model

The repo is scaffolded for single-source publishing:

- `review` editions show paragraph-level source references for editorial checking
- `reader` editions hide those references for cleaner PDF and EPUB reading
- `pod_print` uses the same manuscript order with print styling and front/back matter
