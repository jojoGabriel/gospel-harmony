# Publishing Scaffold

This directory documents the source layout for producing multiple editions from one manuscript.

## Editions

- `review_pdf`: editorial edition with paragraph-level source references visible
- `reader_pdf`: clean reading PDF with source references hidden
- `epub`: reflowable reader edition
- `pod_print`: print-interior PDF for POD workflows

## Source of Truth

- `front_matter/`: title page, copyright, purpose statement, preface
- `sections/`: the narrative itself
- `back_matter/`: method and source notes
- `book.yml`: shared metadata, placeholders, and edition settings
- `manifests/`: assembly order for each edition
- `styles/`: stylesheet layers for print, EPUB, review, and reader targets

## Review References

Review references should be wrapped as:

```html
<span class="review-ref">[Matt 1:18-25]</span>
```

This allows review editions to show them and reader editions to hide them with stylesheet switches.

## Production Notes

- Keep print and EPUB as separate exports derived from the same source files.
- Do not add manual page numbers or running headers to source markdown.
- Keep front matter and back matter in dedicated files so editions can be rearranged without touching the narrative.
- Assign unique ISBNs per format when the publication plan is finalized.
- Store cover assets in `assets/cover/`.
