# Harmonized Gospel

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

## Publishing Model

The repo is scaffolded for single-source publishing:

- `review` editions show paragraph-level source references for editorial checking
- `reader` editions hide those references for cleaner PDF and EPUB reading
- `pod_print` uses the same manuscript order with print styling and front/back matter
