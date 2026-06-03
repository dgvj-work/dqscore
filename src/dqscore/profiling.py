"""Lightweight DataFrame profiling: per-column stats, missingness, outliers."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any, Dict, List, Optional

import pandas as pd

__all__ = ["profile", "Profile"]


@dataclass
class Profile:
    """Result of :func:`profile`, with export helpers."""

    columns: List[Dict[str, Any]]
    n_rows: int
    n_cols: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n_rows": self.n_rows,
            "n_cols": self.n_cols,
            "columns": self.columns,
        }

    def to_frame(self) -> pd.DataFrame:
        """Return the profile as a tidy DataFrame (one row per column)."""
        return pd.DataFrame(self.columns)

    def to_markdown(self) -> str:
        df = self.to_frame()
        cols = [c for c in ["column", "dtype", "missing", "missing_pct",
                            "unique", "distinct_pct", "mean", "min", "max",
                            "outliers_iqr", "top_value"] if c in df.columns]
        lines = [
            f"# Data Profile — {self.n_rows} rows × {self.n_cols} columns",
            "",
            "| " + " | ".join(cols) + " |",
            "| " + " | ".join(["---"] * len(cols)) + " |",
        ]
        for _, row in df[cols].iterrows():
            lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
        return "\n".join(lines)

    def to_html(self, path: Optional[str] = None) -> str:
        table = self.to_frame().to_html(index=False, na_rep="", border=0)
        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Data Profile</title>
<style>
 body {{ font-family:-apple-system,Segoe UI,Roboto,sans-serif; margin:2rem;
        color:#1f2328; }}
 h1 {{ font-size:1.4rem; }}
 table {{ border-collapse:collapse; width:100%; font-size:.88rem; }}
 th,td {{ border-bottom:1px solid #d0d7de; padding:.45rem .6rem;
          text-align:left; }}
 th {{ background:#f6f8fa; position:sticky; top:0; }}
</style></head><body>
<h1>Data Profile — {self.n_rows} rows × {self.n_cols} columns</h1>
{table}
</body></html>"""
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(html)
        return html

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<Profile rows={self.n_rows} cols={self.n_cols}>"


def _round(value: Any, n: int = 4) -> Any:
    try:
        return round(float(value), n)
    except (TypeError, ValueError):
        return value


def profile(df: pd.DataFrame) -> Profile:
    """Build a per-column profile of ``df``.

    For numeric columns this adds descriptive statistics and an IQR-based
    outlier count. For other columns it records the most frequent value.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("profile() expects a pandas DataFrame")

    n = len(df)
    columns: List[Dict[str, Any]] = []

    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        nunique = int(s.nunique(dropna=True))
        info: Dict[str, Any] = {
            "column": str(col),
            "dtype": str(s.dtype),
            "count": int(s.count()),
            "missing": missing,
            "missing_pct": _round(missing / n * 100, 2) if n else 0.0,
            "unique": nunique,
            "distinct_pct": _round(nunique / n * 100, 2) if n else 0.0,
        }

        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s):
            numeric = s.dropna()
            if len(numeric):
                q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
                iqr = q3 - q1
                low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outliers = int(((numeric < low) | (numeric > high)).sum())
                info.update(
                    {
                        "mean": _round(numeric.mean()),
                        "std": _round(numeric.std()),
                        "min": _round(numeric.min()),
                        "q25": _round(q1),
                        "median": _round(numeric.median()),
                        "q75": _round(q3),
                        "max": _round(numeric.max()),
                        "zeros": int((numeric == 0).sum()),
                        "negatives": int((numeric < 0).sum()),
                        "outliers_iqr": outliers,
                    }
                )
        else:
            vc = s.value_counts(dropna=True)
            if len(vc):
                info["top_value"] = str(vc.index[0])
                info["top_freq"] = int(vc.iloc[0])

        columns.append(info)

    return Profile(columns=columns, n_rows=n, n_cols=df.shape[1])
