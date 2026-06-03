import json

import pandas as pd
import pytest

import dqscore as dq


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 3],
            "age": [30, -5, 41, 120],
            "email": ["a@b.com", "bad", "c@d.com", "e@f.com"],
        }
    )


def test_schema_validate_basic(df):
    schema = dq.Schema("people")
    schema.column("id").not_null().unique()
    schema.column("age").in_range(0, 120)
    schema.column("email").matches(r"^[^@]+@[^@]+\.[^@]+$")
    result = schema.validate(df)

    assert not result.passed
    assert result.n_checks == 4
    # id uniqueness fails (two 3s), age has one failure (-5), email has one (bad)
    by = {(r.column, r.check): r for r in result.results}
    assert by[("id", "unique")].n_failing == 2
    assert by[("age", "in_range")].n_failing == 1
    assert by[("email", "matches")].n_failing == 1
    assert by[("id", "not_null")].passed


def test_missing_column_is_reported(df):
    schema = dq.Schema()
    schema.column("does_not_exist").not_null()
    result = schema.validate(df)
    assert not result.passed
    assert result.results[0].check == "column_exists"


def test_passing_schema(df):
    schema = dq.Schema()
    schema.column("id").not_null()
    result = schema.validate(df.drop_duplicates("id"))
    assert result.passed
    assert result.score == 100.0


def test_no_duplicate_rows(df):
    schema = dq.Schema().no_duplicate_rows()
    # the two id==3 rows differ in age, so no full duplicate rows
    assert schema.validate(df).passed
    dup = pd.concat([df.iloc[[0]], df.iloc[[0]]], ignore_index=True)
    assert not dq.Schema().no_duplicate_rows().validate(dup).passed


def test_validate_type_error():
    with pytest.raises(TypeError):
        dq.Schema().validate([1, 2, 3])


def test_report_exports(df):
    schema = dq.Schema("people")
    schema.column("age").in_range(0, 120)
    result = schema.validate(df)

    d = result.to_dict()
    assert d["schema"] == "people"
    assert "results" in d

    parsed = json.loads(result.to_json())
    assert parsed["n_rows"] == 4

    assert "Data Quality Report" in result.summary()
    assert "| Status |" in result.to_markdown()
    assert "<table>" in result.to_html()


def test_profile(df):
    prof = dq.profile(df)
    assert prof.n_rows == 4
    assert prof.n_cols == 3
    frame = prof.to_frame()
    age_row = frame[frame["column"] == "age"].iloc[0]
    assert age_row["missing"] == 0
    assert "mean" in frame.columns
    assert "Data Profile" in prof.to_markdown()
    assert "<table" in prof.to_html()


def test_auto_scan(df):
    result = dq.auto_scan(df)
    # id is duplicated -> uniqueness check should fail
    assert not result.passed
    checks_run = {(r.column, r.check) for r in result.results}
    assert ("id", "unique") in checks_run


def test_auto_scan_clean():
    clean = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
    assert dq.auto_scan(clean).passed


def test_custom_check(df):
    schema = dq.Schema()
    schema.column("age").custom(lambda s: s > 100, name="not_over_100")
    result = schema.validate(df)
    assert not result.passed
    assert result.results[0].check == "not_over_100"
