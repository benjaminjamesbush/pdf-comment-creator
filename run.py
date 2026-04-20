"""CLI entry point: `python run.py path/to/review.yaml`."""

import sys
from pathlib import Path

from engine import build_review


def main():
    if len(sys.argv) != 2:
        print("usage: python run.py path/to/review.yaml", file=sys.stderr)
        sys.exit(2)
    out = build_review(sys.argv[1])
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
