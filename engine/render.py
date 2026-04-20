"""Gutter drawing: page widening, text layout, connector lines, placeholders.

Style constants live here. Override by monkey-patching the module if you need
per-document tweaks, but the default set is tuned for US-letter 612x792 pages.
"""

from __future__ import annotations

import fitz


# --- Geometry ---------------------------------------------------------------

GUTTER_X = 612                  # where gutter starts (right edge of original page)
GUTTER_W = 306                  # gutter width (50% of original 612)
GUTTER_PAD = 10                 # left padding inside gutter
GUTTER_INNER_W = GUTTER_W - 2 * GUTTER_PAD
NEW_PAGE_W = GUTTER_X + GUTTER_W

TOP_MARGIN = 30
BOTTOM_MARGIN = 30
ITEM_GAP = 8                    # vertical gap between stacked items


# --- Typography -------------------------------------------------------------

TITLE_FONT = "hebo"             # Helvetica-Bold
TITLE_SIZE = 12
TITLE_LINE_H = 15

BODY_FONT = "helv"
BODY_SIZE = 11
BODY_LINE_H = 13
BODY_INDENT = 4

TITLE_MAX_W = GUTTER_INNER_W
BODY_MAX_W = GUTTER_INNER_W - BODY_INDENT

PARAGRAPH_GAP = 6
POST_TITLE_GAP = 4


# --- Colors -----------------------------------------------------------------

HIGHLIGHT_COLOR = (1.0, 0.5, 0.55)   # desaturated red
TITLE_COLOR = (1, 0, 0)
BODY_COLOR = (0, 0, 0)
CONNECTOR_COLOR = (1, 0, 0)
CONNECTOR_WIDTH = 1
GUTTER_SEP_COLOR = (0.7, 0.7, 0.7)
GUTTER_SEP_WIDTH = 0.5
PLACEHOLDER_COLOR = (0.55, 0.55, 0.55)
PLACEHOLDER_SPACING = 52        # "NO COMMENTS" repeated every N pt


# --- Word wrapping ----------------------------------------------------------

def wrap_text(text: str, max_width: float, fontname: str, fontsize: float) -> list[str]:
    """Word-wrap text to a pixel width using real font metrics.
    Empty lines in input are preserved as empty lines in output (paragraph breaks).
    """
    out: list[str] = []
    for para in text.split("\n"):
        if not para:
            out.append("")
            continue
        cur = ""
        for word in para.split():
            cand = (cur + " " + word).strip()
            if fitz.get_text_length(cand, fontname=fontname, fontsize=fontsize) <= max_width:
                cur = cand
            else:
                if cur:
                    out.append(cur)
                cur = word
        if cur:
            out.append(cur)
    return out


def body_to_paragraphs(body: str, resolve_refs) -> list[str]:
    """Split a body block into paragraphs (separated by blank lines).
    Resolves cross-refs (#key -> item number) via the provided callback.
    """
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in body.split("\n"):
        line = resolve_refs(raw_line.strip())
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


# --- Measurement + drawing --------------------------------------------------

def measure_item(idx: int, item, resolve_refs) -> int:
    title = f"{idx + 1}. {item.title}"
    h = TITLE_LINE_H * len(wrap_text(title, TITLE_MAX_W, TITLE_FONT, TITLE_SIZE))
    h += POST_TITLE_GAP
    paragraphs = body_to_paragraphs(item.body, resolve_refs)
    for pi, para in enumerate(paragraphs):
        h += BODY_LINE_H * len(wrap_text(para, BODY_MAX_W, BODY_FONT, BODY_SIZE))
        if pi < len(paragraphs) - 1:
            h += PARAGRAPH_GAP
    return h


def draw_item(page, x, y_start, idx, item, resolve_refs):
    y = y_start
    title = f"{idx + 1}. {item.title}"
    for tline in wrap_text(title, TITLE_MAX_W, TITLE_FONT, TITLE_SIZE):
        page.insert_text((x, y + TITLE_SIZE), tline,
                         fontsize=TITLE_SIZE, fontname=TITLE_FONT, color=TITLE_COLOR)
        y += TITLE_LINE_H
    y += POST_TITLE_GAP
    paragraphs = body_to_paragraphs(item.body, resolve_refs)
    for pi, para in enumerate(paragraphs):
        for wline in wrap_text(para, BODY_MAX_W, BODY_FONT, BODY_SIZE):
            page.insert_text((x + BODY_INDENT, y + BODY_SIZE), wline,
                             fontsize=BODY_SIZE, fontname=BODY_FONT, color=BODY_COLOR)
            y += BODY_LINE_H
        if pi < len(paragraphs) - 1:
            y += PARAGRAPH_GAP


def widen_pages(doc, num_pages):
    """Expand each of the first `num_pages` to add a gutter, draw separator."""
    for pn in range(num_pages):
        page = doc[pn]
        h = page.rect.height
        page.set_mediabox(fitz.Rect(0, 0, NEW_PAGE_W, h))
        page.set_cropbox(fitz.Rect(0, 0, NEW_PAGE_W, h))
        page.draw_line(
            fitz.Point(GUTTER_X, 0),
            fitz.Point(GUTTER_X, h),
            color=GUTTER_SEP_COLOR,
            width=GUTTER_SEP_WIDTH,
        )


def draw_connector(page, x, note_y, hl_rect):
    """Thin line from (gutter-left, title-midline) to closest point on highlight."""
    line_mid_y = note_y + TITLE_SIZE / 2 + 1
    cx = max(hl_rect.x0, min(x, hl_rect.x1))
    cy = max(hl_rect.y0, min(line_mid_y, hl_rect.y1))
    page.draw_line(
        fitz.Point(x, line_mid_y),
        fitz.Point(cx, cy),
        color=CONNECTOR_COLOR,
        width=CONNECTOR_WIDTH,
    )


def draw_placeholder(page, x, page_h, text="NO COMMENTS ON THIS PAGE"):
    """Repeated faded label for pages with no items in their gutter."""
    y = 40
    while y < page_h - TOP_MARGIN:
        page.insert_text((x, y), text, fontsize=BODY_SIZE, color=PLACEHOLDER_COLOR)
        y += PLACEHOLDER_SPACING
