import pandas as pd


def validate_required_columns(df, required_columns):
    missing = [col for col in required_columns if col not in df.columns]

    return {
        "passed": len(missing) == 0,
        "missing_columns": missing
    }


def validate_not_null(df, columns):
    failures = {}

    for column in columns:
        if column in df.columns:
            null_count = int(df[column].isna().sum())

            if null_count > 0:
                failures[column] = null_count

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }


def validate_unique(df, column):
    if column not in df.columns:
        return {
            "passed": False,
            "error": f"Column '{column}' not found"
        }

    duplicate_count = int(df[column].duplicated().sum())

    return {
        "passed": bool(duplicate_count == 0),
        "duplicate_count": duplicate_count
    }


def validate_numeric(df, columns):
    failures = {}

    for column in columns:
        if column in df.columns:
            invalid_count = int(
                pd.to_numeric(df[column], errors="coerce").isna().sum()
            )

            if invalid_count > 0:
                failures[column] = invalid_count

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }


def validate_positive(df, columns):
    failures = {}

    for column in columns:
        if column in df.columns:
            values = pd.to_numeric(df[column], errors="coerce")
            negative_count = int((values < 0).sum())

            if negative_count > 0:
                failures[column] = negative_count

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }


def validate_no_duplicates(df):
    duplicate_count = int(df.duplicated().sum())

    return {
        "passed": bool(duplicate_count == 0),
        "duplicate_count": duplicate_count
    }


def validate_date_format(df, column):
    if column not in df.columns:
        return {
            "passed": False,
            "error": f"Column '{column}' not found"
        }

    invalid_count = int(
        pd.to_datetime(df[column], errors="coerce").isna().sum()
    )

    return {
        "passed": bool(invalid_count == 0),
        "invalid_count": invalid_count
    }


def validate_range(df, column, minimum, maximum):
    if column not in df.columns:
        return {
            "passed": False,
            "error": f"Column '{column}' not found"
        }

    values = pd.to_numeric(df[column], errors="coerce")

    invalid_count = int(
        ((values < minimum) | (values > maximum) | values.isna()).sum()
    )

    return {
        "passed": bool(invalid_count == 0),
        "invalid_count": invalid_count
    }


def validate_allowed_values(df, column, allowed_values):
    if column not in df.columns:
        return {
            "passed": False,
            "error": f"Column '{column}' not found"
        }

    invalid_count = int(
        (~df[column].isin(allowed_values)).sum()
    )

    return {
        "passed": bool(invalid_count == 0),
        "invalid_count": invalid_count
    }


def validate_string_length(df, column, minimum=None, maximum=None):
    if column not in df.columns:
        return {
            "passed": False,
            "error": f"Column '{column}' not found"
        }

    lengths = df[column].astype(str).str.len()

    failures = pd.Series(False, index=df.index)

    if minimum is not None:
        failures |= lengths < minimum

    if maximum is not None:
        failures |= lengths > maximum

    invalid_count = int(failures.sum())

    return {
        "passed": bool(invalid_count == 0),
        "invalid_count": invalid_count
    }


def validate_no_blank_strings(df, columns):
    failures = {}

    for column in columns:
        if column in df.columns:
            blank_count = int(
                df[column]
                .fillna("")
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            if blank_count > 0:
                failures[column] = blank_count

    return {
        "passed": len(failures) == 0,
        "failures": failures
    }


def validate_foreign_key(df, column, valid_values):
    if column not in df.columns:
        return {
            "passed": False,
            "error": f"Column '{column}' not found"
        }

    invalid_count = int(
        (~df[column].isin(valid_values)).sum()
    )

    return {
        "passed": bool(invalid_count == 0),
        "invalid_count": invalid_count
    }