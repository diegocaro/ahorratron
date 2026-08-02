#!/usr/bin/env python3
"""Live smoke: scrape Falabella checking + CMR via BancoFalabellaAPI.

Reads CL_FALABELLA_* from bankscrapper/.env (or env). Prints counts only —
never credentials or full movement lists.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(Path("/Users/vitor.dsantos/Documents/PROYECTOS ST-VITTO/bankscrapper/.env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

USER = os.getenv("CL_FALABELLA_USER", "").strip()
PASSWORD = os.getenv("CL_FALABELLA_PASSWORD", "").strip()


def main() -> int:
    if not USER or not PASSWORD:
        print("Missing CL_FALABELLA_USER / CL_FALABELLA_PASSWORD", file=sys.stderr)
        return 1

    from ahorratron.sync_api.institutions.banco_falabella.banco_falabella import (
        BancoFalabellaAPI,
    )
    from ahorratron.sync_api.institutions.banco_falabella.connector import (
        BancoFalabellaConnector,
    )
    from ahorratron.sync_api.institutions.banco_falabella.models import ProductType

    client = BancoFalabellaAPI(USER, PASSWORD)
    connector = BancoFalabellaConnector(client)

    accounts = connector.get_accounts(itemId="live-smoke")
    print(f"accounts: {accounts.total}")
    ok_checking = False
    ok_cmr = False
    for acc in accounts.results:
        txs = connector.get_transactions(accountId=acc.id)
        kind = (
            "checking"
            if acc.subtype.value == "CHECKING_ACCOUNT"
            else "cmr"
            if acc.subtype.value == "CREDIT_CARD"
            else acc.subtype.value
        )
        extra = ""
        if txs.results:
            dates = sorted(t.date for t in txs.results)
            extra = f" range={dates[0].date().isoformat()}…{dates[-1].date().isoformat()}"
        print(
            f"  [{kind}] id=…{acc.id[-4:]} balance={acc.balance:.0f} "
            f"txs={len(txs.results)}{extra}"
        )
        if kind == "checking" and len(txs.results) > 0:
            ok_checking = True
        if kind == "cmr" and len(txs.results) > 0:
            ok_cmr = True

    # also ensure products include both types at client layer
    products = client.get_products().products
    types = {p.type for p in products}
    print(f"product types: {[t.value for t in types]}")

    if ProductType.CHECKING not in types:
        print("FAIL: no checking product", file=sys.stderr)
        return 2
    if ProductType.CREDIT_CARD not in types:
        print("FAIL: no CMR product", file=sys.stderr)
        return 3
    if not ok_checking:
        print("FAIL: checking has 0 movements", file=sys.stderr)
        return 4
    if not ok_cmr:
        print("FAIL: CMR has 0 movements", file=sys.stderr)
        return 5

    print("PASS: checking + CMR scraped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
