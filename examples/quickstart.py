"""A runnable tour of dqscore. Run: python examples/quickstart.py"""
import pandas as pd

import dqscore as dq

# A small, deliberately messy dataset.
df = pd.DataFrame(
    {
        "id": [1, 2, 3, 3, 5],          # duplicate id (3)
        "age": [34, -2, 41, 28, 150],   # -2 and 150 are out of range
        "email": [
            "a@example.com",
            "not-an-email",            # malformed
            "c@example.com",
            "d@example.com",
            None,                       # missing
        ],
        "country": ["US", "US", "CA", "ZZ", "MX"],  # ZZ not allowed
    }
)

print("=" * 60)
print("1) PROFILE")
print("=" * 60)
print(dq.profile(df).to_markdown())

print("\n" + "=" * 60)
print("2) SCHEMA VALIDATION")
print("=" * 60)
schema = dq.Schema("users")
schema.column("id").not_null().unique()
schema.column("age").in_range(0, 120)
schema.column("email").not_null().matches(r"^[^@]+@[^@]+\.[^@]+$")
schema.column("country").in_set(["US", "CA", "MX"])
schema.no_duplicate_rows()

result = schema.validate(df)
print(result.summary())
print(f"\nQuality score: {result.score}%")

# Inspect a specific failure.
for failure in result.failures:
    print(f"  - {failure.column}.{failure.check}: "
          f"sample failing values = {failure.sample_values[:3]}")

print("\n" + "=" * 60)
print("3) ZERO-CONFIG AUTO SCAN")
print("=" * 60)
print(dq.auto_scan(df).summary())

# Write an HTML report you can open in a browser.
result.to_html("dq_report.html")
print("\nWrote dq_report.html")
