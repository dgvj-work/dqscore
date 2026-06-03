# Contributing to dqscore

Thanks for your interest in improving dqscore! Contributions of all sizes are welcome.

## Getting set up

```bash
git clone https://github.com/YOUR_USERNAME/dqscore.git
cd dqscore
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest                  # run the suite
pytest --cov=dqscore     # with coverage
```

Please make sure all tests pass before opening a pull request, and add tests for
any new behaviour.

## Adding a new check

1. Add the row-level function to `src/dqscore/checks.py`. It must accept a
   `pandas.Series` and return a boolean mask where `True` marks a *failing* row.
   Let nulls pass unless the check is specifically about nulls.
2. Expose it as a fluent method on `ColumnSchema` in `src/dqscore/validator.py`.
3. Add a test in `tests/test_checks.py` and update the table in `README.md`.

## Style

- Keep dependencies minimal (pandas only for the core library).
- Prefer small, well-documented functions.
- Follow the existing docstring and type-hint conventions.

## Reporting issues

Open an issue with a minimal reproducible example (a small DataFrame and the
expected vs. actual result). Feature requests are welcome too.
