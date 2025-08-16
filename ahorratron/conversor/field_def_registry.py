from pathlib import Path

BASEDIR = Path(__file__).parent / "field_definitions"
FIELD_DEFINITION_PATHS = {
    "banco_de_chile_cuenta_corriente_txt": BASEDIR
    / "banco_de_chile_cuenta_corriente_txt.json",
    "banco_de_chile_tarjeta_credito_no_facturados_xls": BASEDIR
    / "banco_de_chile_tarjeta_credito_no_facturados_xls.json",
    "banco_de_chile_tarjeta_credito_facturados_xls": BASEDIR
    / "banco_de_chile_tarjeta_credito_facturados_xls.json",
    # Add more mappings here as needed
}
