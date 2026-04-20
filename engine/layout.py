"""Least-squares vertical placement of gutter notes (Pool Adjacent Violators).

Given a list of items with desired center y-coordinates (derived from each
highlight's center) and measured heights, produce actual top-y positions that:

  - preserve input order (items placed top-to-bottom as provided)
  - maintain a minimum gap between items
  - stay within page top/bottom margins
  - minimize Σ (actual_center - desired_center)² — the "fair" tradeoff when
    multiple items compete for the same vertical region

See README for the intuition.
"""

from __future__ import annotations


def compute(measured, page_h, top_margin=30, bottom_margin=30, gap=8):
    """`measured[i]` is (desired_top_y, height). Returns list of actual tops."""
    n = len(measured)
    if n == 0:
        return []
    heights = [m[1] for m in measured]
    desired = [m[0] for m in measured]

    # Clamp boundary-adjacent desireds so LSQ respects margins naturally.
    desired[0] = max(desired[0], top_margin)
    desired[-1] = min(desired[-1], page_h - bottom_margin - heights[-1])

    # Clusters: each is [start_idx, end_idx, top_y].
    clusters = [[i, i, desired[i]] for i in range(n)]

    def recompute_top(start, end):
        total = 0.0
        offset = 0
        for j in range(start, end + 1):
            total += desired[j] - offset
            offset += heights[j] + gap
        return total / (end - start + 1)

    def cluster_bottom(c):
        s, e, top = c
        return top + sum(heights[j] + gap for j in range(s, e)) + heights[e]

    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(clusters) - 1:
            if cluster_bottom(clusters[i]) + gap > clusters[i + 1][2]:
                s = clusters[i][0]
                e = clusters[i + 1][1]
                clusters[i] = [s, e, recompute_top(s, e)]
                clusters.pop(i + 1)
                changed = True
                if i > 0:
                    i -= 1
            else:
                i += 1

    # Hard clamp if LSQ drifted past a page boundary.
    if clusters[0][2] < top_margin:
        clusters[0][2] = top_margin
    last = clusters[-1]
    if cluster_bottom(last) > page_h - bottom_margin:
        span = sum(heights[j] + gap for j in range(last[0], last[1])) + heights[last[1]]
        last[2] = page_h - bottom_margin - span

    ys = [0] * n
    for s, e, top in clusters:
        offset = 0
        for j in range(s, e + 1):
            ys[j] = top + offset
            offset += heights[j] + gap

    # Tidy any violations a hard clamp may have introduced.
    for i in range(1, n):
        min_y = ys[i - 1] + heights[i - 1] + gap
        if ys[i] < min_y:
            ys[i] = min_y
    return ys
