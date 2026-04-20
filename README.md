# pdf-comment-creator

A **human + AI collaboration tool** for reviewing PDFs. A PDF is widened with a right-side gutter, passages are highlighted, and comments are placed in the new margin — each connected to its highlighted passage by a thin line. Comments are written as YAML, which means iterating on a review with an AI assistant produces small, reviewable git diffs.

## How to use it (with an AI assistant)

The intended workflow is to start a session with an AI (Claude, ChatGPT, Copilot, etc.) and have it drive the repo on your behalf. Paste a prompt like this into your AI assistant:

> Hi Claude, I'd like to review a PDF with you.
>
> 1. Clone `https://github.com/benjaminjamesbush/pdf-comment-creator` into a new folder (or "Use this template" on GitHub if I want a clean history).
> 2. Read the README so you understand how the tool works.
> 3. I'll drop my source PDF into the repo root. Update `review.yaml` so it points at that file.
> 4. Read the PDF and draft an initial set of review comments in `review.yaml`. Use the four highlight types (`search`, `line_contains`, `row_span`, `rect`) as appropriate.
> 5. Run `python run.py review.yaml` and open the output in my browser.
> 6. Let's iterate — I'll give feedback ("rewrite item 3", "this is too strongly worded", "add a comment on page 5 about X") and you adjust the YAML and re-render.
> 7. Commit regularly so we have a history of the review's evolution.

Most iteration happens on `review.yaml` — add/remove/reword items, change highlight anchors, reorder, refine. The AI edits the config, re-runs the engine, and shows you the new output. Because the config is text, every change is a small git diff.

## Trying it without an AI

If you want to see the tool in action before starting a real review:

```bash
git clone https://github.com/benjaminjamesbush/pdf-comment-creator.git
cd pdf-comment-creator
pip install -r requirements.txt
python run.py examples/sample/review.yaml
```

Open `examples/sample/output.pdf` — a self-aware tutorial whose own margin comments explain how the tool works.

## Clone-per-PDF workflow

This repo is designed to be cloned (or used as a GitHub template) **once per document** you want to review. Each review ends up as its own self-contained repo: source PDF, `review.yaml`, engine code, and git history of the review's evolution. Collaborators can reproduce your output with a single `git clone` + `python run.py review.yaml`.

Because the engine travels with each review, upgrades don't propagate automatically. Pull from upstream when you want a newer engine; pin by commit if you want reproducibility.

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
