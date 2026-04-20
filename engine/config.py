"""YAML config loader + schema validation.

A review YAML has three top-level keys:

    source: path to input PDF (relative to the YAML file)
    output: path to output PDF (relative to the YAML file)
    items:  list of review items (see Item schema below)

Each item:

    key:       stable identifier (referenced by #key in body text)
    page:      1-indexed page number
    title:     short heading (rendered bold red in the gutter)
    highlight: dict describing what to highlight — see HIGHLIGHT_TYPES
    body:      prose (paragraphs separated by blank lines)

Highlight types:

    {type: search,         text: "..."}
    {type: line_contains,  contains: "..."}
    {type: row_span,       left: "...", right: "..."}
    {type: rect,           x0: N, y0: N, x1: N, y1: N}

All are page-scoped to the item's `page` unless the highlight dict provides
its own `page` (rare).
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path


HIGHLIGHT_TYPES = {"search", "line_contains", "row_span", "rect"}


@dataclass
class Item:
    key: str
    page: int
    title: str
    highlight: dict
    body: str = ""


@dataclass
class ReviewConfig:
    source: Path
    output: Path
    items: list[Item] = field(default_factory=list)


def _validate_highlight(h: dict, where: str) -> None:
    if not isinstance(h, dict) or "type" not in h:
        raise ValueError(f"{where}: highlight must be a dict with a 'type' field")
    t = h["type"]
    if t not in HIGHLIGHT_TYPES:
        raise ValueError(
            f"{where}: highlight type '{t}' is not one of {sorted(HIGHLIGHT_TYPES)}"
        )
    required = {
        "search": ["text"],
        "line_contains": ["contains"],
        "row_span": ["left", "right"],
        "rect": ["x0", "y0", "x1", "y1"],
    }[t]
    missing = [k for k in required if k not in h]
    if missing:
        raise ValueError(f"{where}: highlight type '{t}' missing fields: {missing}")


def load(path: str | Path) -> ReviewConfig:
    path = Path(path).resolve()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    base = path.parent

    for key in ("source", "output", "items"):
        if key not in raw:
            raise ValueError(f"config missing required key '{key}'")

    items: list[Item] = []
    seen_keys: set[str] = set()
    for i, entry in enumerate(raw["items"]):
        where = f"items[{i}]"
        for k in ("key", "page", "title", "highlight"):
            if k not in entry:
                raise ValueError(f"{where}: missing field '{k}'")
        if entry["key"] in seen_keys:
            raise ValueError(f"{where}: duplicate key '{entry['key']}'")
        seen_keys.add(entry["key"])
        _validate_highlight(entry["highlight"], where)
        items.append(
            Item(
                key=entry["key"],
                page=int(entry["page"]),
                title=entry["title"],
                highlight=entry["highlight"],
                body=entry.get("body", ""),
            )
        )

    return ReviewConfig(
        source=(base / raw["source"]).resolve(),
        output=(base / raw["output"]).resolve(),
        items=items,
    )
