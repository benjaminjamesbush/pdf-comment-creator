"""Top-level orchestration: load config, apply highlights, lay out gutter notes."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import fitz

from . import highlights as hl
from . import layout
from . import render
from .config import Item, ReviewConfig, load


def build_review(config_path: str | Path) -> Path:
    """Read a review YAML and write the commented output PDF. Returns the output path."""
    cfg = load(config_path)
    doc = fitz.open(cfg.source)

    # 1. Apply highlights, collect canonical anchor rect per item
    link_targets: dict[str, tuple[int, fitz.Rect]] = {}
    for item in cfg.items:
        spec = item.highlight
        page_num = spec.get("page", item.page) - 1   # 1-indexed -> 0-indexed
        page = doc[page_num]
        anchor = hl.apply(page, spec, render.HIGHLIGHT_COLOR)
        if anchor is None:
            print(f"warning: highlight for '{item.key}' produced no match; skipping")
            continue
        link_targets[item.key] = (page_num, anchor)

    # 2. Sort items by (page, anchor y) so gutter order follows highlight order
    def anchor_y(item: Item) -> float:
        tgt = link_targets.get(item.key)
        return tgt[1].y0 if tgt else float("inf")

    ordered_items = sorted(cfg.items, key=lambda it: (it.page, anchor_y(it)))
    key_to_num = {it.key: i + 1 for i, it in enumerate(ordered_items)}

    def resolve_refs(text: str) -> str:
        for key, num in key_to_num.items():
            text = text.replace(f"#{key}", str(num))
        return text

    # 3. Widen original pages to add the gutter
    num_original = len(doc)
    render.widen_pages(doc, num_original)

    # 4. Draw placeholder on pages with no items
    items_by_page: dict[int, list] = defaultdict(list)
    for i, item in enumerate(ordered_items):
        items_by_page[item.page].append((i, item))
    for pn in range(num_original):
        if (pn + 1) in items_by_page:
            continue
        page = doc[pn]
        render.draw_placeholder(page, render.GUTTER_X + render.GUTTER_PAD, page.rect.height)

    # 5. Lay out and draw each page's gutter notes
    for page_num, entries in items_by_page.items():
        page = doc[page_num - 1]
        page_h = page.rect.height
        x = render.GUTTER_X + render.GUTTER_PAD

        measured = []
        for idx, item in entries:
            h = render.measure_item(idx, item, resolve_refs)
            tgt = link_targets.get(item.key)
            if tgt:
                hl_rect = tgt[1]
                desired_y = (hl_rect.y0 + hl_rect.y1) / 2 - h / 2
            else:
                desired_y = render.TOP_MARGIN
            measured.append((desired_y, h))

        ys = layout.compute(
            measured, page_h,
            top_margin=render.TOP_MARGIN,
            bottom_margin=render.BOTTOM_MARGIN,
            gap=render.ITEM_GAP,
        )

        for (idx, item), y in zip(entries, ys):
            tgt = link_targets.get(item.key)
            if tgt:
                render.draw_connector(page, x, y, tgt[1])
            render.draw_item(page, x, y, idx, item, resolve_refs)

    # 6. Save
    cfg.output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(cfg.output)
    doc.close()
    return cfg.output
