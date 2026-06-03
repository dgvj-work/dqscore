import numpy as np
import pandas as pd

from dqscore import checks


def test_not_null():
    s = pd.Series([1, None, 3])
    assert list(checks.not_null(s)) == [False, True, False]


def test_unique_ignores_nulls():
    s = pd.Series([1, 1, 2, None, None])
    # the two 1s fail; nulls are left to not_null
    assert list(checks.unique(s)) == [True, True, False, False, False]


def test_in_range_inclusive():
    s = pd.Series([0, 5, 10, 11, None])
    mask = checks.in_range(s, 0, 10, inclusive=True)
    assert list(mask) == [False, False, False, True, False]


def test_in_range_exclusive():
    s = pd.Series([0, 5, 10])
    mask = checks.in_range(s, 0, 10, inclusive=False)
    assert list(mask) == [True, False, True]


def test_in_range_non_numeric_fails():
    s = pd.Series(["a", "5", None])
    mask = checks.in_range(s, 0, 10)
    assert list(mask) == [True, False, False]


def test_in_set():
    s = pd.Series(["a", "b", "z", None])
    mask = checks.in_set(s, ["a", "b"])
    assert list(mask) == [False, False, True, False]


def test_matches():
    s = pd.Series(["a@b.com", "bad", None])
    mask = checks.matches(s, r"^[^@]+@[^@]+\.[^@]+$")
    assert list(mask) == [False, True, False]


def test_is_integer():
    s = pd.Series([1, 2.0, 2.5, "x", None])
    mask = checks.is_integer(s)
    assert list(mask) == [False, False, True, True, False]


def test_is_datetime():
    s = pd.Series(["2020-01-01", "not-a-date", None])
    mask = checks.is_datetime(s)
    assert list(mask) == [False, True, False]


def test_string_length():
    s = pd.Series(["ab", "abcd", "abcdef", None])
    mask = checks.string_length(s, min_len=3, max_len=5)
    assert list(mask) == [True, False, True, False]


def test_no_duplicate_rows():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    mask = checks.no_duplicate_rows(df)
    assert list(mask) == [True, True, False]
