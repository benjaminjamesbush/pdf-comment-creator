# pdf-comment-creator

A **human + AI collaboration tool** for reviewing PDFs. Pages are widened with a right-side gutter; passages are highlighted; aligned comments live in the new margin, each connected to its highlight by a thin line. Comments are stored as YAML, so iterating with an AI assistant produces small, reviewable git diffs.

---

## For humans: paste this into your AI assistant

```
I'd like to review a PDF with you using pdf-comment-creator:
https://github.com/benjaminjamesbush/pdf-comment-creator

Please read its README and guide me through setup.
```

That's it. The AI will ask you where to clone, where your PDF is, and when you're ready to start. Everything else — editing the config, running the engine, showing you the output, committing — is on the AI.

---

## For AI assistants: how to drive a session

You are the driver for this review. The human has pasted the prompt above and is waiting for you to take charge. Follow this playbook.

### 1. Orient yourself

Clone the repo (or make sure you have a local copy), then look at **`examples/sample/output.pdf`** — it's a self-aware tutorial whose own margin comments explain how the tool works. Read it before writing any YAML. The sample also demonstrates each of the four highlight types in action.

Also read **`examples/sample/review.yaml`** alongside the tutorial output so you can see how the YAML maps to what's rendered on the page.

### 2. Onboard the user

Ask the user (one thing at a time is fine):

- **Where should I clone this?** Suggest a path like `~/pdf-reviews/<short-name>/` if they don't have a preference. Use GitHub's "Use this template" if they want a clean git history in their review repo.
- **Where is the source PDF?** Get the path. Copy it into the cloned repo (root is fine) and update `source:` and `output:` in `review.yaml` accordingly.
- **Any context you want me to know?** The user may have specific concerns, a summary of the document, or known issues to flag. Capture this — it shapes the review.
- **Ready to dig in?** Open the PDF, read it carefully, then tell the user you're ready and invite them to start walking through it with you.

### 3. Iterate on `review.yaml`

The review is a conversation. Don't draft a bunch of comments unilaterally — let them emerge from discussion. When a comment is agreed on, add it to `review.yaml`, run `python run.py review.yaml`, and open the output for the user to see.

Rhythm:
- User says something → you propose wording → user approves or refines → you write it into YAML → re-render → user reviews output → repeat.
- Use cross-references (`#key`) in body text when one comment refers to another by number; the engine resolves them at render time, so reorderings don't break refs.
- Commit after every meaningful change so the git log narrates the review.

### 4. YAML schema

```yaml
source: path/to/source.pdf        # relative to the YAML file
output: path/to/output.pdf

items:
  - key: my_comment               # stable identifier; referenced by #my_comment
    page: 3                       # 1-indexed page number
    title: "Short heading"        # bold red at top of the comment
    highlights:                   # one or more passages to highlight
      - type: search
        text: "the exact passage"
    body: |
      Paragraphs of commentary. Write naturally — the engine wraps to the
      gutter width using real font metrics.

      Blank lines between paragraphs produce paragraph breaks in the output.
```

### 5. Highlight types

| Type | When to use | Required fields |
|------|-------------|-----------------|
| `search` | ~90% of cases; exact phrase match | `text` |
| `line_contains` | When `search` fails (ligature glyphs, text extraction quirks) | `contains` |
| `row_span` | Full-width form-row highlights (question + answer options on one line) | `left`, `right` (anchor strings on the same line) |
| `rect` | Escape hatch — explicit coordinates (brittle against source changes) | `x0`, `y0`, `x1`, `y1` |

`search` returns the union of all fragment rectangles PyMuPDF finds, so the connector line aims at the full span even when the phrase is split across multiple rects.

### 6. What the engine does (so you can explain it if asked)

1. Widens every page by 50% on the right to add a gutter. Original content is untouched.
2. Applies highlights on the left side (one or more per item) in a desaturated red. The first highlight is the connector anchor.
3. Sorts items by (page, anchor y) so gutter order follows highlight order top-to-bottom.
4. Lays out each page's gutter notes with **least-squares placement** under ordering and no-overlap constraints. When items compete for the same vertical region, each drifts slightly from its ideal y so every comment ends up as close to its highlight as the constraints allow — "fairness wins" over first-come-first-serve.
5. Draws a thin connector line from each comment's title to the closest point on its highlight.
6. Fills pages with no items with a faded `NO COMMENTS ON THIS PAGE` label so layout stays consistent.

### 7. Behavior you should adopt

- **Don't unilaterally add comments.** Every comment emerges from the conversation with the user.
- **Show the output after every change.** Don't batch multiple edits before re-rendering.
- **When the user pushes back, revise or remove.** Reviews are opinionated — if a comment doesn't feel right to them, it shouldn't stay.
- **Watch for natural cross-references.** If a comment mentions "item N," use `#key` so reorderings stay correct.
- **Advocate for the user when the review is adversarial.** If the review is going to be shared with someone (school district, vendor, etc.), don't phrase things in ways that give the other side ammunition. Ask if you're uncertain.
- **Keep titles short.** They render in ~10pt bold; long titles wrap awkwardly.
- **Commit regularly.** The git log becomes the record of how the review evolved.

### 8. Known limitations (mention if relevant)

- Only tested with US-letter pages (612×792 pt).
- If a page has more comments than can fit vertically, the last ones may overlap — the layout algorithm does best-effort compression but doesn't guarantee fit.
- `search` is exact-match (no regex).
- No Python escape hatch for custom highlight logic. If the four built-in types don't fit a case, adding a new type to `engine/highlights.py` is the right move.

---

## Trying the tool without an AI

If you want to render the sample yourself before starting a real review:

```bash
git clone https://github.com/benjaminjamesbush/pdf-comment-creator.git
cd pdf-comment-creator
pip install -r requirements.txt
python run.py examples/sample/review.yaml
```

Open `examples/sample/output.pdf` to see the tutorial.

## Project layout

```
pdf-comment-creator/
├── run.py                       # CLI entry point
├── engine/
│   ├── orchestrator.py          # top-level build_review()
│   ├── config.py                # YAML loader + schema validation
│   ├── highlights.py            # handlers for each highlight type
│   ├── layout.py                # least-squares placement
│   └── render.py                # drawing + style constants
├── examples/sample/
│   ├── generate_source.py       # regenerates the tutorial source.pdf
│   ├── source.pdf               # tracked
│   ├── review.yaml              # tracked — demonstrates each highlight type
│   └── output.pdf               # gitignored; run `python run.py` to produce
├── requirements.txt
└── README.md
```

Style constants live at the top of `engine/render.py`: gutter width, margins, fonts, sizes, colors. No per-document style override in YAML — layout is a tool concern, not a content concern.
