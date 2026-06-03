# dqscore

> A lightweight **data quality toolkit for pandas** — profile any DataFrame, declare
> expectations with a fluent schema, or run a zero-config scan. No heavy dependencies,
> no config files required.

[![CI](https://github.com/YOUR_USERNAME/dqscore/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/dqscore/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

`dqscore` helps you catch the boring-but-costly data problems — nulls where there
shouldn't be any, duplicate keys, out-of-range values, malformed strings — before
they reach a model, a dashboard, or a stakeholder.

---

## Why dqscore?

- **Tiny surface area.** Three things to learn: `profile`, `Schema`, `auto_scan`.
- **Readable reports.** Every result exports to dict, JSON, Markdown, or styled HTML.
- **Scoreable.** Each validation produces a 0–100 quality score for dashboards/CI.
- **CLI included.** `dqscore scan data.csv` returns a non-zero exit code on failure,
  so it drops straight into a pipeline or pre-commit hook.
- **One dependency:** pandas.

---

## Installation

```bash
pip install dqscore
```

Or install the latest from source:

```bash
git clone https://github.com/YOUR_USERNAME/dqscore.git
cd dqscore
pip install -e ".[dev]"
```

---

## Quick start

### 1. Profile a DataFrame

```python
import pandas as pd
import dqscore as dq

df = pd.read_csv("customers.csv")
profile = dq.profile(df)

print(profile.to_markdown())   # per-column stats
profile.to_html("profile.html")
```

### 2. Validate against a schema

```python
schema = dq.Schema("customers")
schema.column("id").not_null().unique()
schema.column("age").in_range(0, 120)
schema.column("email").matches(r"^[^@]+@[^@]+\.[^@]+$")
schema.column("country").in_set(["US", "CA", "MX"])
schema.no_duplicate_rows()

result = schema.validate(df)

print(result.summary())        # human-readable report
print("Quality score:", result.score)
result.to_html("dq_report.html")

if not result.passed:
    raise SystemExit("Data quality checks failed")
```

### 3. Zero-config scan

When you just want a quick read on a new file:

```python
result = dq.auto_scan(df)       # checks nulls, duplicate keys, duplicate rows
print(result.summary())
```

---

## Command line

```bash
# Profile every column
dqscore profile data.csv --html profile.html

# Quick quality scan (exit code 1 if it fails — great for CI)
dqscore scan data.csv --json report.json
dqscore scan data.csv --max-null-pct 5
```

---

## Available checks

| Method                              | Fails when…                                  |
| ----------------------------------- | -------------------------------------------- |
| `not_null()`                        | value is null / NaN / NaT                    |
| `unique()`                          | a non-null value occurs more than once       |
| `in_range(min, max, inclusive)`     | numeric value is outside the bounds          |
| `in_set([...])`                     | value is not one of the allowed values       |
| `matches(pattern, full_match)`      | string does not match the regex              |
| `is_numeric()` / `is_integer()`     | value can't be parsed as a number / integer  |
| `is_datetime(fmt)`                  | value can't be parsed as a date/time         |
| `string_length(min_len, max_len)`   | string length is out of bounds               |
| `custom(fn, name)`                  | your function returns `True` for a row        |
| `Schema.no_duplicate_rows(subset)`  | rows are exact duplicates                     |

Checks chain on a column and most let nulls pass, so `not_null()` stays the single
source of truth for missing values:

```python
schema.column("score").not_null().is_numeric().in_range(0, 100)
```

---

## Reports & scoring

A `ValidationResult` gives you:

- `result.passed` — `True`/`False`
- `result.score` — percentage of checks passed (0–100)
- `result.failures` — only the failing checks (with sample failing values & indices)
- `result.summary()` / `to_markdown()` / `to_json()` / `to_html(path)`

---

## Contributing

Contributions and feedback are very welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).
Found a bug or want a new check? [Open an issue](https://github.com/YOUR_USERNAME/dqscore/issues).

## License

[MIT](LICENSE)
