"""Generate the self-aware tutorial PDF that the sample review annotates.

Run this once (or whenever the tutorial copy changes):

    python examples/sample/generate_source.py

Writes `source.pdf` in this directory.
"""

from pathlib import Path

import fitz


PAGE_W = 612
PAGE_H = 792
MARGIN = 54
COL_R = PAGE_W - MARGIN

FONT_TITLE = "hebo"
FONT_BODY = "helv"
FONT_ITAL = "heit"
BLACK = (0, 0, 0)
GREY = (0.4, 0.4, 0.4)


def layout_text(page, y, text, fontname=FONT_BODY, fontsize=11, color=BLACK,
                line_h=15, paragraph_gap=7, x=MARGIN, max_w=COL_R - MARGIN):
    """Draw wrapped paragraphs starting at y; return new y."""
    for para in text.split("\n\n"):
        for wline in wrap(para.strip().replace("\n", " "), max_w, fontname, fontsize):
            page.insert_text((x, y), wline, fontname=fontname, fontsize=fontsize, color=color)
            y += line_h
        y += paragraph_gap
    return y


def wrap(text, max_w, fontname, fontsize):
    out, cur = [], ""
    for word in text.split():
        cand = (cur + " " + word).strip()
        if fitz.get_text_length(cand, fontname=fontname, fontsize=fontsize) <= max_w:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def draw_heading(page, y, text, size=18):
    page.insert_text((MARGIN, y), text, fontname=FONT_TITLE, fontsize=size, color=BLACK)
    return y + size + 8


def draw_subheading(page, y, text):
    page.insert_text((MARGIN, y), text, fontname=FONT_TITLE, fontsize=13, color=BLACK)
    return y + 20


def draw_rule(page, y):
    page.draw_line(fitz.Point(MARGIN, y), fitz.Point(COL_R, y), color=GREY, width=0.5)
    return y + 10


def draw_checkbox_row(page, y, label, options, checked_idx):
    """Draw `label: [ ] opt1  [ ] opt2  [x] opt3` style row; return new y.
    Used to demonstrate the `row_span` highlight type.
    """
    page.insert_text((MARGIN, y), label, fontname=FONT_TITLE, fontsize=11, color=BLACK)
    x = MARGIN + fitz.get_text_length(label, fontname=FONT_TITLE, fontsize=11) + 12
    for i, opt in enumerate(options):
        mark = "[X]" if i == checked_idx else "[ ]"
        page.insert_text((x, y), f"{mark} {opt}", fontname=FONT_BODY, fontsize=11, color=BLACK)
        x += fitz.get_text_length(f"{mark} {opt}  ", fontname=FONT_BODY, fontsize=11)
    return y + 22


def build():
    doc = fitz.open()

    # --- Page 1: What this tool does --------------------------------------
    p = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = 72
    y = draw_heading(p, y, "pdf-comment-creator")
    y = layout_text(
        p, y,
        "This document is the sample source PDF for the pdf-comment-creator project. "
        "If you are reading the reviewed output of this document (with comments in the "
        "right-side gutter), everything you see was produced from a YAML config and a "
        "small Python engine.",
        fontname=FONT_ITAL, color=GREY,
    )
    y += 8
    y = draw_rule(p, y)
    y += 8

    y = draw_subheading(p, y, "What it does")
    y = layout_text(
        p, y,
        "The engine takes a source PDF and a YAML file describing review comments. "
        "It widens each page by 50% to add a right-side gutter, draws red highlights "
        "on the passages you care about, and writes your comments in the new margin "
        "with a thin line connecting each comment to its highlighted passage.\n\n"
        "The goal is a single PDF artifact that a reader can scan linearly: "
        "original text on the left, your commentary on the right, no jumping around.",
    )

    y += 8
    y = draw_subheading(p, y, "The clone-per-PDF workflow")
    y = layout_text(
        p, y,
        "To review a document, clone this repository (or use GitHub's 'Use this template' "
        "button for a clean history), drop your source PDF in, edit review.yaml, and "
        "run `python run.py review.yaml`. Commit iteratively as you refine your review. "
        "The review repo becomes a self-contained artifact that collaborators can clone "
        "and work on.",
    )

    y += 8
    y = draw_subheading(p, y, "Self-aware tutorial")
    y = layout_text(
        p, y,
        "The comments you see in the margin of THIS document were written to demonstrate "
        "the four highlight types the engine supports. Each comment points at the text "
        "it describes. Read them in order to understand what the tool can do.",
    )

    # --- Page 2: The four highlight types --------------------------------
    p = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = 72
    y = draw_heading(p, y, "The four highlight types")
    y = layout_text(
        p, y,
        "Every review item in the YAML config has a `highlight:` field specifying how "
        "to locate the passage it annotates. Four types are supported.",
        fontname=FONT_ITAL, color=GREY,
    )
    y += 8

    y = draw_subheading(p, y, "search")
    y = layout_text(
        p, y,
        "The simplest and most common type. Provide a text phrase; the engine calls "
        "page.search_for and highlights every rectangle returned. Fragment rectangles "
        "(which PyMuPDF sometimes returns for ligatures or kerning) are unioned into a "
        "single anchor rect for link targeting and connector lines.",
    )
    y += 4

    y = draw_subheading(p, y, "line_contains")
    y = layout_text(
        p, y,
        "Sometimes page.search_for fails to match text that contains ligature glyphs "
        "(for example, the 'ti' ligature in 'Autism'). This type walks page.get_text "
        "line by line and returns the bounding box of the first line containing the "
        "given substring. Use it when search doesn't work.",
    )
    y += 4

    y = draw_subheading(p, y, "row_span")
    y = layout_text(
        p, y,
        "For form rows: provide a left anchor and a right anchor. The engine finds "
        "both, uses the left anchor's y range, and spans from the left anchor's x0 to "
        "the right anchor's x1. This produces a horizontal highlight across a full "
        "form row containing a question and answer options.",
    )
    y += 4
    y = draw_checkbox_row(p, y, "Primary shipping method:",
                          ["Standard", "Expedited", "Overnight"], checked_idx=1)

    y += 4
    y = draw_subheading(p, y, "rect")
    y = layout_text(
        p, y,
        "The escape hatch: provide explicit x0, y0, x1, y1 coordinates. Use when none "
        "of the above types work. Rare, but available.",
    )

    # --- Page 3: Layout behavior ------------------------------------------
    p = doc.new_page(width=PAGE_W, height=PAGE_H)
    y = 72
    y = draw_heading(p, y, "How the gutter lays itself out")
    y = layout_text(
        p, y,
        "When multiple comments anchor to nearby passages, they compete for the same "
        "vertical region in the gutter. The engine resolves this with a least-squares "
        "pool-adjacent-violators algorithm: it minimizes the sum of squared vertical "
        "displacements from each comment's ideal position, subject to no-overlap and "
        "page-margin constraints.",
    )

    y += 8
    y = draw_subheading(p, y, "Fair tradeoffs")
    y = layout_text(
        p, y,
        "A naive first-come-first-serve layout gives the topmost comment its perfect "
        "alignment and pushes everyone else down. Least-squares distributes the "
        "displacement: the topmost comment drifts up slightly so the one below can "
        "stay closer to its anchor. On average, every comment ends up closer to its "
        "highlight than it would with the greedy approach.",
    )

    y += 8
    y = draw_subheading(p, y, "Text wrapping")
    y = layout_text(
        p, y,
        "Comment bodies are written as natural paragraphs in the YAML config, with "
        "blank lines separating paragraphs. The engine wraps to the gutter width "
        "using real font metrics from fitz.get_text_length, so authors don't think "
        "about line breaks at all.",
    )

    y += 8
    y = draw_subheading(p, y, "Pages with no comments")
    y = layout_text(
        p, y,
        "Pages that have no review items still get the widened gutter, filled with a "
        "faded 'NO COMMENTS ON THIS PAGE' label repeated vertically, so the page count "
        "and layout stay consistent across the document.",
    )

    # Save
    out = Path(__file__).parent / "source.pdf"
    doc.save(out)
    doc.close()
    print(f"wrote {out}")


if __name__ == "__main__":
    build()
