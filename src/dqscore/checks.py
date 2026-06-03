"""Low-level data quality checks.

Every check takes a :class:`pandas.Series` (or DataFrame, for frame-level
checks) and returns a boolean mask aligned to the input where ``True`` marks a
*failing* row. Null handling is deliberate: most checks let nulls pass so that
``not_null`` is the single source of truth for missing values. Combine checks to
express richer expectations.
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Optional

import pandas as pd

__all__ = [
    "not_null",
    "unique",
    "in_range",
    "in_set",
    "matches",
    "is_numeric",
    "is_integer",
    "is_datetime",
    "string_length",
    "no_duplicate_rows",
]


def _as_bool_mask(mask: pd.Series, index: pd.Index) -> pd.Series:
    """Coerce a mask to a clean boolean Series aligned to ``index``."""
    return pd.Series(mask, index=index).fillna(False).astype(bool)


def not_null(series: pd.Series) -> pd.Series:
    """Fail rows whose value is null / NaN / NaT."""
    return series.isna()


def unique(series: pd.Series) -> pd.Series:
    """Fail rows whose (non-null) value appears more than once."""
    duplicated = series.duplicated(keep=False)
    return _as_bool_mask(duplicated & series.notna(), series.index)


def in_range(
    series: pd.Series,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    inclusive: bool = True,
) -> pd.Series:
    """Fail rows outside ``[min_value, max_value]``.

    Non-numeric, non-null values fail as well. Nulls pass (use ``not_null``).
    """
    numeric = pd.to_numeric(series, errors="coerce")
    fail = pd.Series(False, index=series.index)
    if min_value is not None:
        fail |= (numeric < min_value) if inclusive else (numeric <= min_value)
    if max_value is not None:
        fail |= (numeric > max_value) if inclusive else (numeric >= max_value)
    non_numeric = numeric.isna() & series.notna()
    fail |= non_numeric
    return _as_bool_mask(fail, series.index)


def in_set(series: pd.Series, allowed: Iterable[Any]) -> pd.Series:
    """Fail rows whose (non-null) value is not in ``allowed``."""
    allowed_set = set(allowed)
    fail = ~series.isin(allowed_set) & series.notna()
    return _as_bool_mask(fail, series.index)


def matches(series: pd.Series, pattern: str, full_match: bool = False) -> pd.Series:
    """Fail rows whose (non-null) string value does not match ``pattern``."""
    compiled = re.compile(pattern)
    finder = compiled.fullmatch if full_match else compiled.search

    def _fails(value: Any) -> bool:
        if pd.isna(value):
            return False
        return finder(str(value)) is None

    return _as_bool_mask(series.map(_fails), series.index)


def is_numeric(series: pd.Series) -> pd.Series:
    """Fail non-null values that cannot be parsed as numbers."""
    coerced = pd.to_numeric(series, errors="coerce")
    return _as_bool_mask(coerced.isna() & series.notna(), series.index)


def is_integer(series: pd.Series) -> pd.Series:
    """Fail non-null values that are not whole numbers."""
    coerced = pd.to_numeric(series, errors="coerce")
    non_numeric = coerced.isna() & series.notna()
    non_integer = coerced.notna() & (coerced % 1 != 0)
    return _as_bool_mask(non_numeric | non_integer, series.index)


def is_datetime(series: pd.Series, fmt: Optional[str] = None) -> pd.Series:
    """Fail non-null values that cannot be parsed as dates/times."""
    coerced = pd.to_datetime(series, errors="coerce", format=fmt)
    return _as_bool_mask(coerced.isna() & series.notna(), series.index)


def string_length(
    series: pd.Series,
    min_len: Optional[int] = None,
    max_len: Optional[int] = None,
) -> pd.Series:
    """Fail non-null values whose string length is outside the bounds."""
    lengths = series.dropna().astype(str).str.len()
    fail = pd.Series(False, index=series.index)
    if min_len is not None:
        fail.loc[lengths.index] |= lengths < min_len
    if max_len is not None:
        fail.loc[lengths.index] |= lengths > max_len
    return _as_bool_mask(fail, series.index)


def no_duplicate_rows(
    df: pd.DataFrame, subset: Optional[Iterable[str]] = None
) -> pd.Series:
    """Fail rows that are exact duplicates (optionally over ``subset``)."""
    subset_list = list(subset) if subset is not None else None
    return _as_bool_mask(df.duplicated(subset=subset_list, keep=False), df.index)
