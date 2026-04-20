# pdf-comment-creator

Annotate a PDF by widening each page with a right-side gutter, highlighting passages of interest, and placing aligned comments in the new margin. Each comment is connected to its highlighted passage by a thin line.

Designed for human + AI collaboration. Reviews are written as YAML; iterating on a review is a git-friendly activity with small, reviewable diffs.

## Quick start

```bash
git clone https://github.com/benjaminjamesbush/pdf-comment-creator.git my-review
cd my-review
pip install -r requirements.txt

# Regenerate the sample output
python examples/sample/generate_source.py
python run.py examples/sample/review.yaml
```

Open `examples/sample/output.pdf` to see the self-aware tutorial — a PDF whose own margin comments explain how the tool works.

## Clone-per-PDF workflow

This repo is designed to be cloned (or used as a GitHub template) once per document you want to review.

1. **"Use this template"** on GitHub for a clean history, or clone + `git remote rename origin upstream` + add your own origin.
2. Drop your source PDF into the repo root (or a subdirectory — the YAML is referenced relative to its own location).
3. Create a `review.yaml` modeled on `examples/sample/review.yaml`.
4. Run `python run.py review.yaml` to produce the annotated output.
5. Commit iteratively as you refine your review. The git history becomes the record of how the review evolved.

The engine code travels with your review. Anyone who clones your review repo can reproduce the annotated PDF with the same engine version that produced it.

## Writing a review

A `review.yaml` has three top-level keys:

```yaml
source: path/to/source.pdf       # relative to the YAML file
output: path/to/output.pdf       # where to write the annotated PDF

items:
  - key: my_comment               # stable identifier, referenced by #my_comment
    page: 3                       # 1-indexed page number
    title: "Short heading"        # rendered bold red at the top of the comment
    highlights:                   # one or more passages to highlight (see below)
      - type: search
        text: "the exact passage"
    body: |
      Paragraphs of commentary go here. Write naturally — the engine
      wraps to the gutter width using real font metrics.

      Blank lines between paragraphs produce paragraph breaks in the
      rendered output.
```

### Highlight types

| Type | When to use | Required fields |
|------|-------------|-----------------|
| `search` | 90% of cases; exact phrase match | `text` |
| `line_contains` | When `search` fails (ligature glyphs, etc.) | `contains` |
| `row_span` | Full-width form-row highlights | `left`, `right` (anchor strings on the same line) |
| `rect` | Escape hatch — explicit coordinates | `x0`, `y0`, `x1`, `y1` |

### Cross-references

Use `#key` in body text to reference another item by its current number. The engine resolves these at render time, so re-ordering items doesn't break references.

## What the engine does

1. **Widens every page** by 50% on the right to create a gutter (original content is untouched).
2. **Applies highlights** on the left side (one or more per item) in the configured pinkish-red; the first highlight is the anchor for the connector line.
3. **Sorts items by (page, anchor y)** so gutter order follows highlight order top-to-bottom.
4. **Lays out each page's gutter notes** using least-squares placement with ordering and no-overlap constraints. When items compete for the same vertical region, each drifts slightly from its ideal y so every comment ends up as close to its highlight as the constraints allow.
5. **Draws connector lines** from each comment's title to the closest point on its highlight.
6. **Fills empty pages** with a faded "NO COMMENTS ON THIS PAGE" marker so the visual layout stays consistent.

## Project layout

```
pdf-comment-creator/
├── run.py                    # CLI entry point
├── engine/
│   ├── orchestrator.py       # top-level build_review()
│   ├── config.py             # YAML loader + schema
│   ├── highlights.py         # highlight type handlers
│   ├── layout.py             # least-squares placement
│   └── render.py             # drawing + style constants
├── examples/
│   └── sample/
│       ├── generate_source.py  # regenerates the tutorial source.pdf
│       ├── source.pdf          # tracked — the tutorial PDF
│       ├── review.yaml         # tracked — demonstrates each highlight type
│       └── output.pdf          # gitignored — run `python run.py` to produce
├── requirements.txt
└── README.md
```

## Style tweaks

All layout constants live at the top of `engine/render.py`: gutter width, margins, fonts, sizes, colors. Edit the module directly; there is no per-document style override in YAML (layout is a tool concern, not a content concern).

## Limitations

- Only tested with US-letter pages. Other sizes likely work but aren't guaranteed.
- If a page has more comments than can fit vertically, the last ones will overlap. The algorithm does best-effort compression; pathological crowding is not handled.
- `search` is exact-match (no regex). If you need fuzzy or case-insensitive matching, that's a future extension.
- No Python escape hatch for custom highlight logic. If you hit a case the four built-in types can't handle, open an issue or add a new type to `engine/highlights.py`.
