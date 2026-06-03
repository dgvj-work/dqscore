# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-03

### Added
- `dq.profile(df)` — per-column profiling (dtype, missingness, uniqueness,
  numeric statistics, IQR outlier counts) with dict / DataFrame / Markdown /
  HTML exports.
- `dq.Schema` — fluent validation API with checks: `not_null`, `unique`,
  `in_range`, `in_set`, `matches`, `is_numeric`, `is_integer`, `is_datetime`,
  `string_length`, `custom`, and frame-level `no_duplicate_rows`.
- `ValidationResult` with a 0–100 quality score and summary / JSON / Markdown /
  HTML exports.
- `dq.auto_scan(df)` — zero-config quality scan (nulls, duplicate keys,
  duplicate rows).
- `dqscore` command-line interface with `profile` and `scan` subcommands.
