from __future__ import annotations

import argparse
import sys

from .agent import run


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the public job search agent.")
    parser.add_argument("--dry-run", action="store_true", help="Use sample data and avoid network/API calls.")
    args = parser.parse_args()
    output_path = run(dry_run=args.dry_run)
    print(f"Created spreadsheet: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
