"""CLI: input stays local; no model pickle or outbound network access."""

import argparse
import json
import sys
from pathlib import Path

from .core import load, select


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a batch for human annotation.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--budget", type=int, default=5)
    parser.add_argument("--diversity", type=float, default=0.35)
    args = parser.parse_args()
    try:
        report = select(load(args.input), args.budget, args.diversity)
    except (OSError, ValueError, RecursionError, OverflowError):
        print(
            "Invalid input or unreadable file; see README for schema and bounds.", file=sys.stderr
        )
        return 2
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
