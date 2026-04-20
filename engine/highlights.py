"""Highlight type handlers.

Each handler takes a fitz.Page and a highlight spec (dict from YAML), applies
the highlight annotations to the page, and returns the *union* rect that the
reviewer should treat as the canonical anchor for link targets and connector
lines. Returning None means "no valid highlight found"; the caller decides
how to surface that (currently: warn and skip).
"""

from __future__ import annotations

import fitz


def _union(rects):
    if not rects:
        return None
    u = fitz.Rect(rects[0])
    for r in rects[1:]:
        u |= r
    return u


def apply(page: fitz.Page, spec: dict, color) -> fitz.Rect | None:
    """Dispatch on spec['type'] and highlight the page. Return union rect."""
    t = spec["type"]
    rects = _resolve_rects(page, spec)
    if not rects:
        return None
    for r in rects:
        annot = page.add_highlight_annot(r)
        annot.set_colors(stroke=color)
        annot.update()
    return _union(rects)


def _resolve_rects(page: fitz.Page, spec: dict) -> list[fitz.Rect]:
    t = spec["type"]
    if t == "search":
        return list(page.search_for(spec["text"]))
    if t == "line_contains":
        return [r] if (r := _line_bbox(page, spec["contains"])) else []
    if t == "row_span":
        return [r] if (r := _row_span(page, spec["left"], spec["right"])) else []
    if t == "rect":
        return [fitz.Rect(spec["x0"], spec["y0"], spec["x1"], spec["y1"])]
    raise ValueError(f"unknown highlight type: {t}")


def _line_bbox(page: fitz.Page, contains: str) -> fitz.Rect | None:
    """Return the bbox of the first text line that contains `contains`."""
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"])
            if contains in text:
                return fitz.Rect(line["bbox"])
    return None


def _row_span(page: fitz.Page, left: str, right: str) -> fitz.Rect | None:
    """Rect spanning from the left anchor's x0 to the right anchor's x1,
    using the left anchor's y range. Useful for highlighting a form row
    based on two pieces of label text on the same line.
    """
    left_rects = page.search_for(left)
    right_rects = page.search_for(right)
    if not left_rects or not right_rects:
        return None
    l = left_rects[0]
    # Pick the right-anchor rect on the same visual line as the left anchor
    r = next(
        (rr for rr in right_rects if abs(rr.y0 - l.y0) < 6),
        right_rects[0],
    )
    return fitz.Rect(l.x0, l.y0, r.x1, max(l.y1, r.y1))
