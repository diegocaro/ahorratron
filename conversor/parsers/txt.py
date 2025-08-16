from copy import deepcopy
from typing import Any

import pandas as pd


def get_expected_length(field_definitions: dict[str, Any]) -> int:
    """Calculate the expected length of a fixed-width record based on field definitions."""
    return sum(field["length"] for field in field_definitions.values())


def fit_to_grow_definitions(
    field_definitions: dict[str, Any], new_line_length: int
) -> dict[str, Any]:
    expected = get_expected_length(field_definitions)
    diff = new_line_length - expected
    ans = deepcopy(field_definitions)
    found = False
    for field, field_def in field_definitions.items():
        if field_def.get("grow_to_fit", False):
            ans[field]["length"] += diff
            found = True
            continue
        if found:
            ans[field]["start"] += diff
    return ans


def read_fixed_width_file(
    lines: list[str], field_definitions: dict[str, Any]
) -> pd.DataFrame:
    records = []
    expected_length = get_expected_length(field_definitions)
    for line in lines:
        if not line.strip():
            continue
        new_field_definitions = field_definitions
        if len(line) > expected_length:
            new_field_definitions = fit_to_grow_definitions(
                field_definitions, len(line)
            )
        record = {}
        for field_name, field_def in new_field_definitions.items():
            start_idx = field_def["start"] - 1
            end_idx = start_idx + field_def["length"]
            if start_idx < len(line) and end_idx <= len(line):
                raw_value = line[start_idx:end_idx].strip()
            else:
                raw_value = ""
            if field_def["type"] == "date" and raw_value:
                try:
                    value = pd.to_datetime(raw_value, format=field_def["format"])
                except (ValueError, TypeError):
                    value = raw_value  # type: ignore
            elif field_def["type"] == "decimal" and raw_value:
                try:
                    value = float(raw_value.strip())  # type: ignore
                except ValueError:
                    value = 0.0  # type: ignore
            else:
                value = raw_value  # type: ignore
            record[field_name] = value
        records.append(record)
    df = pd.DataFrame(records)
    if "sign" in df.columns and "amount" in df.columns:
        df["amount"] = df.apply(
            lambda row: -row["amount"] if row["sign"] == "-" else row["amount"], axis=1
        )
    return df
