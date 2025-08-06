from typing import Any

import pandas as pd


def read_xls(file_path: str, field_definitions: dict[str, Any]) -> pd.DataFrame:
    """
    Read a credit card statement from an Excel file and convert it to a DataFrame.
    """

    skiprows = field_definitions.get("__config__", {}).get("skiprows", 0)
    df = pd.read_excel(file_path, skiprows=skiprows)
    df.columns = df.columns.str.strip()

    mapped_columns = {
        value["column_name"]: key
        for key, value in field_definitions.items()
        if "column_name" in value
    }

    df = df.rename(columns=mapped_columns)
    df = df[list(mapped_columns.values())]  # Keep only mapped columns

    amount_is_payment_if_contains = field_definitions["amount"].get(
        "amount_is_payment_if_contains"
    )
    if amount_is_payment_if_contains:
        colname = amount_is_payment_if_contains.get("column_name", "description")
        value = amount_is_payment_if_contains.get("value", "")
        df["amount"] = df.apply(
            lambda row: (-row["amount"] if value in row[colname] else row["amount"]),
            axis=1,
        )

    reverse_amount = field_definitions.get("amount", {}).get("reverse_amount", False)
    if reverse_amount:
        df["amount"] = -df["amount"]

    df["date"] = pd.to_datetime(df["date"], format=field_definitions["date"]["format"])
    return df
