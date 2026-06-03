"""Result objects for validation runs, with scoring and export helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from html import escape
from typing import Any, Dict, List, Optional

__all__ = ["CheckResult", "ValidationResult"]


@dataclass
class CheckResult:
    """Outcome of a single check against a single column (or the frame)."""

    check: str
    column: str
    passed: bool
    n_failing: int
    n_total: int
    params: Dict[str, Any] = field(default_factory=dict)
    failing_index: List[Any] = field(default_factory=list)
    sample_values: List[Any] = field(default_factory=list)
    message: str = ""

    @property
    def pass_rate(self) -> float:
        """Fraction of rows that satisfied this check (0.0 - 1.0)."""
        if self.n_total == 0:
            return 1.0
        return (self.n_total - self.n_failing) / self.n_total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check": self.check,
            "column": self.column,
            "passed": self.passed,
            "n_failing": self.n_failing,
            "n_total": self.n_total,
            "pass_rate": round(self.pass_rate, 4),
            "params": self.params,
            "failing_index": [str(i) for i in self.failing_index],
            "sample_values": [_safe(v) for v in self.sample_values],
            "message": self.message,
        }


@dataclass
class ValidationResult:
    """Aggregated outcome of validating a DataFrame against a schema."""

    results: List[CheckResult]
    n_rows: int
    schema_name: str = "schema"

    # -- summary properties -------------------------------------------------
    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def n_checks(self) -> int:
        return len(self.results)

    @property
    def n_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def n_failed(self) -> int:
        return self.n_checks - self.n_passed

    @property
    def score(self) -> float:
        """Percentage of checks that passed (0 - 100)."""
        if not self.results:
            return 100.0
        return round(self.n_passed / self.n_checks * 100, 2)

    @property
    def failures(self) -> List[CheckResult]:
        return [r for r in self.results if not r.passed]

    # -- exports ------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema_name,
            "passed": self.passed,
            "score": self.score,
            "n_rows": self.n_rows,
            "n_checks": self.n_checks,
            "n_passed": self.n_passed,
            "n_failed": self.n_failed,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=_safe)

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"Data Quality Report  -  schema: {self.schema_name}",
            "=" * 52,
            f"Status : {status}",
            f"Score  : {self.score}%  ({self.n_passed}/{self.n_checks} checks)",
            f"Rows   : {self.n_rows}",
            "-" * 52,
        ]
        for r in self.results:
            mark = "PASS" if r.passed else "FAIL"
            detail = "" if r.passed else f"  ({r.n_failing} failing)"
            lines.append(f"[{mark}] {r.column}.{r.check}{detail}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [
            f"# Data Quality Report — `{self.schema_name}`",
            "",
            f"**Status:** {status}  ·  **Score:** {self.score}%  "
            f"·  **Checks:** {self.n_passed}/{self.n_checks} passed  "
            f"·  **Rows:** {self.n_rows}",
            "",
            "| Status | Column | Check | Failing | Pass rate |",
            "| :----: | ------ | ----- | ------: | --------: |",
        ]
        for r in self.results:
            mark = "✅" if r.passed else "❌"
            lines.append(
                f"| {mark} | `{r.column}` | {r.check} | "
                f"{r.n_failing} | {r.pass_rate:.1%} |"
            )
        return "\n".join(lines)

    def to_html(self, path: Optional[str] = None) -> str:
        rows = []
        for r in self.results:
            color = "#1a7f37" if r.passed else "#cf222e"
            mark = "PASS" if r.passed else "FAIL"
            rows.append(
                f"<tr><td style='color:{color};font-weight:600'>{mark}</td>"
                f"<td><code>{escape(str(r.column))}</code></td>"
                f"<td>{escape(r.check)}</td>"
                f"<td style='text-align:right'>{r.n_failing}</td>"
                f"<td style='text-align:right'>{r.pass_rate:.1%}</td></tr>"
            )
        status = "PASSED" if self.passed else "FAILED"
        status_color = "#1a7f37" if self.passed else "#cf222e"
        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>DQ Report - {escape(self.schema_name)}</title>
<style>
 body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif;
        margin: 2rem; color: #1f2328; }}
 h1 {{ font-size: 1.4rem; }}
 .badge {{ display:inline-block; padding:.2rem .6rem; border-radius:6px;
           color:#fff; font-weight:600; background:{status_color}; }}
 table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
 th, td {{ border-bottom: 1px solid #d0d7de; padding: .5rem .75rem;
           text-align: left; font-size: .92rem; }}
 th {{ background:#f6f8fa; }}
 .meta {{ color:#57606a; margin:.5rem 0 1rem; }}
</style></head><body>
<h1>Data Quality Report — {escape(self.schema_name)}</h1>
<p><span class="badge">{status}</span></p>
<p class="meta">Score {self.score}% · {self.n_passed}/{self.n_checks} checks
 passed · {self.n_rows} rows</p>
<table><thead><tr><th>Status</th><th>Column</th><th>Check</th>
<th style="text-align:right">Failing</th>
<th style="text-align:right">Pass rate</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>"""
        if path:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(html)
        return html

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"<ValidationResult passed={self.passed} score={self.score}% "
            f"checks={self.n_passed}/{self.n_checks}>"
        )


def _safe(value: Any) -> Any:
    """Make numpy / pandas scalars JSON-serialisable."""
    try:
        import numpy as np

        if isinstance(value, np.generic):
            return value.item()
    except Exception:  # pragma: no cover
        pass
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)
