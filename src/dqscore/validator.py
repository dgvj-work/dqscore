"""A small, fluent schema API for declaring expectations and validating data.

Example
-------
>>> import dqscore as dq
>>> schema = dq.Schema("customers")
>>> schema.column("id").not_null().unique()
>>> schema.column("age").in_range(0, 120)
>>> schema.column("email").matches(r"^[^@]+@[^@]+\\.[^@]+$")
>>> schema.no_duplicate_rows()
>>> result = schema.validate(df)          # doctest: +SKIP
>>> print(result.summary())               # doctest: +SKIP
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import pandas as pd

from . import checks
from .report import CheckResult, ValidationResult

__all__ = ["Schema", "ColumnSchema"]

# A registered check: display name, function(series)->mask, params for the report
_ColumnCheck = Tuple[str, Callable[[pd.Series], pd.Series], Dict[str, Any]]
_FrameCheck = Tuple[str, Callable[[pd.DataFrame], pd.Series], Dict[str, Any]]


class ColumnSchema:
    """Collects the checks declared for a single column. Methods chain."""

    def __init__(self, name: str, parent: "Schema") -> None:
        self.name = name
        self._parent = parent
        self._checks: List[_ColumnCheck] = []
        self.required = True

    def _add(self, name: str, fn: Callable[[pd.Series], pd.Series], **params: Any):
        self._checks.append((name, fn, params))
        return self

    # -- expectations -------------------------------------------------------
    def not_null(self) -> "ColumnSchema":
        return self._add("not_null", checks.not_null)

    def unique(self) -> "ColumnSchema":
        return self._add("unique", checks.unique)

    def in_range(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        inclusive: bool = True,
    ) -> "ColumnSchema":
        return self._add(
            "in_range",
            lambda s: checks.in_range(s, min_value, max_value, inclusive),
            min_value=min_value,
            max_value=max_value,
            inclusive=inclusive,
        )

    def in_set(self, allowed: Iterable[Any]) -> "ColumnSchema":
        allowed = list(allowed)
        return self._add("in_set", lambda s: checks.in_set(s, allowed), allowed=allowed)

    def matches(self, pattern: str, full_match: bool = False) -> "ColumnSchema":
        return self._add(
            "matches",
            lambda s: checks.matches(s, pattern, full_match),
            pattern=pattern,
            full_match=full_match,
        )

    def is_numeric(self) -> "ColumnSchema":
        return self._add("is_numeric", checks.is_numeric)

    def is_integer(self) -> "ColumnSchema":
        return self._add("is_integer", checks.is_integer)

    def is_datetime(self, fmt: Optional[str] = None) -> "ColumnSchema":
        return self._add("is_datetime", lambda s: checks.is_datetime(s, fmt), fmt=fmt)

    def string_length(
        self, min_len: Optional[int] = None, max_len: Optional[int] = None
    ) -> "ColumnSchema":
        return self._add(
            "string_length",
            lambda s: checks.string_length(s, min_len, max_len),
            min_len=min_len,
            max_len=max_len,
        )

    def custom(
        self, fn: Callable[[pd.Series], pd.Series], name: str = "custom"
    ) -> "ColumnSchema":
        """Register a user function returning a mask (``True`` == failing)."""
        return self._add(name, fn)

    # -- convenience to keep chaining onto the schema ----------------------
    def column(self, name: str) -> "ColumnSchema":
        return self._parent.column(name)


class Schema:
    """A collection of column- and frame-level expectations."""

    def __init__(self, name: str = "schema") -> None:
        self.name = name
        self._columns: Dict[str, ColumnSchema] = {}
        self._frame_checks: List[_FrameCheck] = []

    def column(self, name: str) -> ColumnSchema:
        """Return (creating if needed) the schema for ``name``."""
        if name not in self._columns:
            self._columns[name] = ColumnSchema(name, self)
        return self._columns[name]

    def no_duplicate_rows(
        self, subset: Optional[Iterable[str]] = None
    ) -> "Schema":
        subset = list(subset) if subset is not None else None
        self._frame_checks.append(
            (
                "no_duplicate_rows",
                lambda df: checks.no_duplicate_rows(df, subset),
                {"subset": subset},
            )
        )
        return self

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Run every declared check against ``df`` and collect the results."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("validate() expects a pandas DataFrame")

        results: List[CheckResult] = []
        n_total = len(df)

        for col_name, col in self._columns.items():
            if col_name not in df.columns:
                if col.required:
                    results.append(
                        CheckResult(
                            check="column_exists",
                            column=col_name,
                            passed=False,
                            n_failing=n_total,
                            n_total=n_total,
                            message=f"Column '{col_name}' is missing.",
                        )
                    )
                continue

            series = df[col_name]
            for check_name, fn, params in col._checks:
                mask = checks._as_bool_mask(fn(series), series.index)
                n_failing = int(mask.sum())
                failing_idx = list(df.index[mask][:10])
                results.append(
                    CheckResult(
                        check=check_name,
                        column=col_name,
                        passed=n_failing == 0,
                        n_failing=n_failing,
                        n_total=n_total,
                        params=params,
                        failing_index=failing_idx,
                        sample_values=list(series[mask].head(10)),
                    )
                )

        for check_name, fn, params in self._frame_checks:
            mask = checks._as_bool_mask(fn(df), df.index)
            n_failing = int(mask.sum())
            results.append(
                CheckResult(
                    check=check_name,
                    column="<frame>",
                    passed=n_failing == 0,
                    n_failing=n_failing,
                    n_total=n_total,
                    params=params,
                    failing_index=list(df.index[mask][:10]),
                )
            )

        return ValidationResult(results=results, n_rows=n_total, schema_name=self.name)
