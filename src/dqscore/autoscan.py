"""Zero-config quality scan: infer sensible default checks for any DataFrame."""
from __future__ import annotations

from typing import Optional

import pandas as pd

from .report import ValidationResult
from .validator import Schema

__all__ = ["auto_scan"]


def _looks_like_id(name: str) -> bool:
    lowered = str(name).lower()
    return lowered == "id" or lowered.endswith("_id") or lowered.endswith("id")


def auto_scan(
    df: pd.DataFrame,
    max_null_pct: float = 0.0,
    name: str = "auto_scan",
) -> ValidationResult:
    """Run a quick, opinionated quality scan with no schema required.

    Heuristics applied:

    * every column is expected to have at most ``max_null_pct`` percent nulls;
    * columns that look like identifiers (``id`` / ``*_id``) are expected to be
      unique;
    * the frame is expected to have no fully duplicated rows.

    Parameters
    ----------
    df:
        The DataFrame to scan.
    max_null_pct:
        Allowed percentage of nulls per column before the column's null check
        fails. ``0.0`` means "no nulls allowed".
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("auto_scan() expects a pandas DataFrame")

    n = len(df)
    threshold = max_null_pct / 100.0
    schema = Schema(name)

    for col in df.columns:
        series = df[col]
        null_frac = series.isna().mean() if n else 0.0
        if null_frac > threshold:
            # Flag missingness explicitly via the not_null check.
            schema.column(col).not_null()
        if _looks_like_id(col):
            # Identifier-like columns are expected to be unique; this surfaces
            # accidental duplicate keys, a common data quality defect.
            schema.column(col).unique()

    schema.no_duplicate_rows()
    return schema.validate(df)
