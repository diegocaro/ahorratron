import json

import pytest

from conversor.field_def_registry import FIELD_DEFINITION_PATHS
from conversor.parsers.txt import read_fixed_width_file


@pytest.fixture(scope="module")
def field_definitions():
    field_def_path = FIELD_DEFINITION_PATHS["banco_de_chile_cuenta_corriente_txt"]
    with open(field_def_path) as f:
        return json.load(f)


def get_example_lines():
    # Masked/made-up account and serial numbers, but keep structure
    return [
        "0000000000020250629980000000        0000000000000000000000+000RETENCIONES + 1 DIA                          S2025062900000",
        "0000000000020250629970000000        0000000000000000000000+000RETENCIONES 1 DIA                            S2025062900000",
        "0000000000020250629990000000        0000000000000000646503+000SALDO CONTABLE                               S2025062900000",
        "0000000000020250630000000000000000000000000000000000017840+000Traspaso A Cuenta:XXXXXXXXXXXX               C2025063000000",
        "0000000000020250630000000000000000000000000000000000500000+000Traspaso De:John Doe                         A2025063000000",
        # ... more lines ...
        # Line with grow_to_fit bug: description is longer than usual
        "0000000000020250630000000000000000000000000000000000012345+000Pago:una descripcion muy larga que excede el largo normal de la descripcion y debe crecer el campo para ajustarse a esto C2025063000000",
    ]


def test_read_fixed_width_file_handles_basic_and_grow_to_fit(field_definitions):
    lines = get_example_lines()
    df = read_fixed_width_file(lines, field_definitions)
    # Check that all lines are parsed
    assert len(df) == len(lines)
    # Check that the description field is not truncated for the last line
    long_desc = df.iloc[-1]["description"]
    assert "muy larga que excede" in long_desc
    # Check that amounts are parsed as float
    assert df["amount"].apply(lambda x: isinstance(x, float)).all()
    # Check that masked account is present
    assert df.iloc[0]["account"] == "00000000000"
    # Check that issue_date is parsed correctly for each line
    expected_dates = [
        "2025-06-29",
        "2025-06-29",
        "2025-06-29",
        "2025-06-30",
        "2025-06-30",
        "2025-06-30",
    ]
    actual_dates = [str(d)[:10] for d in df["issue_date"]]
    assert actual_dates == expected_dates
