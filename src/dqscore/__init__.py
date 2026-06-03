"""dqscore — a lightweight data quality toolkit for pandas.

Quick start
-----------
>>> import pandas as pd
>>> import dqscore as dq
>>> df = pd.DataFrame({"id": [1, 2, 2], "age": [30, -1, 41]})
>>> result = dq.auto_scan(df)
>>> result.passed
False

Declare expectations explicitly with a :class:`~dqscore.Schema`::

    schema = dq.Schema("people")
    schema.column("id").not_null().unique()
    schema.column("age").in_range(0, 120)
    report = schema.validate(df)
    print(report.summary())
"""
from __future__ import annotations

from . import checks
from .autoscan import auto_scan
from .profiling import Profile, profile
from .report import CheckResult, ValidationResult
from .validator import ColumnSchema, Schema

__version__ = "0.1.0"

__all__ = [
    "Schema",
    "ColumnSchema",
    "profile",
    "Profile",
    "auto_scan",
    "ValidationResult",
    "CheckResult",
    "checks",
    "__version__",
]
