"""Command-line interface: ``dqscore profile|scan path.csv``."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

import pandas as pd

from . import __version__, auto_scan, profile


def _read(path: str, sep: Optional[str]) -> pd.DataFrame:
    return pd.read_csv(path, sep=sep) if sep else pd.read_csv(path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dqscore",
        description="Lightweight data quality toolkit for tabular data.",
    )
    parser.add_argument("--version", action="version",
                        version=f"dqscore {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("path", help="Path to a CSV/TSV file.")
    common.add_argument("--sep", default=None, help="Field separator (e.g. '\\t').")
    common.add_argument("--html", metavar="FILE", help="Write an HTML report.")
    common.add_argument("--json", metavar="FILE", help="Write a JSON report.")

    p_profile = sub.add_parser("profile", parents=[common],
                               help="Profile every column of the file.")
    p_profile.add_argument("--markdown", metavar="FILE",
                           help="Write a Markdown profile.")

    p_scan = sub.add_parser("scan", parents=[common],
                            help="Run a zero-config quality scan.")
    p_scan.add_argument("--max-null-pct", type=float, default=0.0,
                        help="Allowed %% of nulls per column (default 0).")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        df = _read(args.path, args.sep)
    except Exception as exc:  # pragma: no cover - user input errors
        print(f"error: could not read {args.path}: {exc}", file=sys.stderr)
        return 2

    if args.command == "profile":
        prof = profile(df)
        print(prof.to_markdown())
        if getattr(args, "markdown", None):
            with open(args.markdown, "w", encoding="utf-8") as fh:
                fh.write(prof.to_markdown())
        if args.html:
            prof.to_html(args.html)
        if args.json:
            import json

            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(prof.to_dict(), fh, indent=2, default=str)
        return 0

    # scan
    result = auto_scan(df, max_null_pct=args.max_null_pct)
    print(result.summary())
    if args.html:
        result.to_html(args.html)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(result.to_json())
    return 0 if result.passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
