import pandas as pd

from src.etl.validator import (
    validate_required_columns,
    validate_not_null,
    validate_unique,
    validate_numeric,
    validate_positive,
    validate_no_duplicates,
    validate_date_format,
    validate_range,
    validate_allowed_values,
    validate_string_length,
    validate_no_blank_strings,
    validate_foreign_key,
)


def test_required_columns_pass():
    df = pd.DataFrame({
        "id": [1, 2],
        "name": ["A", "B"]
    })

    result = validate_required_columns(df, ["id", "name"])

    assert result["passed"] is True


def test_required_columns_fail():
    df = pd.DataFrame({
        "id": [1, 2]
    })

    result = validate_required_columns(df, ["id", "name"])

    assert result["passed"] is False


def test_not_null_pass():
    df = pd.DataFrame({
        "id": [1, 2, 3]
    })

    result = validate_not_null(df, ["id"])

    assert result["passed"] is True


def test_not_null_fail():
    df = pd.DataFrame({
        "id": [1, None, 3]
    })

    result = validate_not_null(df, ["id"])

    assert result["passed"] is False


def test_unique_pass():
    df = pd.DataFrame({
        "id": [1, 2, 3]
    })

    result = validate_unique(df, "id")

    assert result["passed"] is True


def test_unique_fail():
    df = pd.DataFrame({
        "id": [1, 2, 2]
    })

    result = validate_unique(df, "id")

    assert result["passed"] is False


def test_numeric_pass():
    df = pd.DataFrame({
        "price": [100, 200, 300]
    })

    result = validate_numeric(df, ["price"])

    assert result["passed"] is True


def test_numeric_fail():
    df = pd.DataFrame({
        "price": [100, "abc", 300]
    })

    result = validate_numeric(df, ["price"])

    assert result["passed"] is False


def test_positive_pass():
    df = pd.DataFrame({
        "price": [100, 200, 300]
    })

    result = validate_positive(df, ["price"])

    assert result["passed"] is True


def test_positive_fail():
    df = pd.DataFrame({
        "price": [100, -200, 300]
    })

    result = validate_positive(df, ["price"])

    assert result["passed"] is False

def test_no_duplicates_pass():
    df = pd.DataFrame({
        "id": [1, 2, 3]
    })

    result = validate_no_duplicates(df)

    assert result["passed"] is True


def test_no_duplicates_fail():
    df = pd.DataFrame({
        "id": [1, 2, 2]
    })

    result = validate_no_duplicates(df)

    assert result["passed"] is False


def test_date_format_pass():
    df = pd.DataFrame({
        "date": ["2024-01-01", "2024-02-01"]
    })

    result = validate_date_format(df, "date")

    assert result["passed"] is True


def test_date_format_fail():
    df = pd.DataFrame({
        "date": ["2024-01-01", "invalid"]
    })

    result = validate_date_format(df, "date")

    assert result["passed"] is False


def test_range_pass():
    df = pd.DataFrame({
        "score": [10, 50, 90]
    })

    result = validate_range(df, "score", 0, 100)

    assert result["passed"] is True


def test_range_fail():
    df = pd.DataFrame({
        "score": [10, 150, 90]
    })

    result = validate_range(df, "score", 0, 100)

    assert result["passed"] is False


def test_allowed_values_pass():
    df = pd.DataFrame({
        "type": ["BUY", "SELL"]
    })

    result = validate_allowed_values(
        df,
        "type",
        ["BUY", "SELL"]
    )

    assert result["passed"] is True


def test_allowed_values_fail():
    df = pd.DataFrame({
        "type": ["BUY", "HOLD"]
    })

    result = validate_allowed_values(
        df,
        "type",
        ["BUY", "SELL"]
    )

    assert result["passed"] is False


def test_string_length_pass():
    df = pd.DataFrame({
        "ticker": ["ABB", "TCS"]
    })

    result = validate_string_length(
        df,
        "ticker",
        minimum=2,
        maximum=10
    )

    assert result["passed"] is True


def test_string_length_fail():
    df = pd.DataFrame({
        "ticker": ["A", "THISISTOOLONG"]
    })

    result = validate_string_length(
        df,
        "ticker",
        minimum=2,
        maximum=10
    )

    assert result["passed"] is False


def test_no_blank_strings_pass():
    df = pd.DataFrame({
        "name": ["ABB", "TCS"]
    })

    result = validate_no_blank_strings(df, ["name"])

    assert result["passed"] is True


def test_no_blank_strings_fail():
    df = pd.DataFrame({
        "name": ["ABB", "   "]
    })

    result = validate_no_blank_strings(df, ["name"])

    assert result["passed"] is False


def test_foreign_key_pass():
    df = pd.DataFrame({
        "company_id": ["ABB", "TCS"]
    })

    result = validate_foreign_key(
        df,
        "company_id",
        {"ABB", "TCS", "INFY"}
    )

    assert result["passed"] is True


def test_foreign_key_fail():
    df = pd.DataFrame({
        "company_id": ["ABB", "XYZ"]
    })

    result = validate_foreign_key(
        df,
        "company_id",
        {"ABB", "TCS", "INFY"}
    )

    assert result["passed"] is False