import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from ahorratron.field_def_registry import FIELD_DEFINITION_PATHS
from ahorratron.parsers.txt import read_fixed_width_file


def convert_to_actual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the DataFrame to a format suitable for actual bank transactions.
    """
    out = df.copy()
    out["amount"] = out.apply(
        lambda row: -row["amount"] if row["transaction_type"] == "C" else row["amount"],
        axis=1,
    )
    out = out[~out["transaction_type"].isin(["S"])]  # solo abonos y cargos
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out["notes"] = out["description"]
    out = out[["date", "amount", "description", "notes"]]
    return out


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Convert a bank TXT file to actual CSV format. "
            "Reads from stdin if txt_file is '-' or omitted, "
            "writes to stdout if --output is '-' or omitted."
        )
    )
    parser.add_argument(
        "txt_file",
        nargs="?",
        default="-",
        help="Path to the input TXT file or '-' for stdin (default: '-')",
    )
    parser.add_argument(
        "--fields",
        default="banco_de_chile_cuenta_corriente_txt",
        help="Field definition key or path (default: banco_de_chile_cuenta_corriente_txt)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="-",
        help="Output CSV file name or '-' for stdout (default: '-')",
    )
    args = parser.parse_args()

    # Resolve field definitions path
    fields_arg = args.fields
    fields_path = FIELD_DEFINITION_PATHS.get(fields_arg, Path(fields_arg))
    try:
        with open(fields_path, encoding="utf8") as f:
            field_definitions = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading field definitions: {e}", file=sys.stderr)
        sys.exit(1)

    # Read lines from TXT file or stdin
    try:
        if args.txt_file == "-":
            lines = sys.stdin.read().splitlines()
        else:
            with open(args.txt_file, "rt", encoding="utf8") as f:
                lines = f.read().splitlines()
    except OSError as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse TXT file
    try:
        df = read_fixed_width_file(lines, field_definitions)
        actual_df = convert_to_actual(df)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error parsing or converting: {e}", file=sys.stderr)
        sys.exit(1)

    # Write to output file or stdout
    try:
        if args.output == "-":
            actual_df.to_csv(sys.stdout, index=False)
        else:
            actual_df.to_csv(args.output, index=False)
    except OSError as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

    # No print on success, exit 0


if __name__ == "__main__":
    main()
