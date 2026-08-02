#!/usr/bin/env python3
"""HTTP smoke against local Ahorratrón API: /auth → /accounts → /v2/transactions.

Expects uvicorn on AHORRATRON_BASE (default http://127.0.0.1:8000) with
JWE/JWT env loaded. Credentials from CL_FALABELLA_* (bankscrapper/.env).
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
load_dotenv(Path("/Users/vitor.dsantos/Documents/PROYECTOS ST-VITTO/bankscrapper/.env"))

BASE = os.getenv("AHORRATRON_BASE", "http://127.0.0.1:8000").rstrip("/")
USER = os.getenv("CL_FALABELLA_USER", "").strip()
PASSWORD = os.getenv("CL_FALABELLA_PASSWORD", "").strip()
# Verify SSL only if not using self-signed docker cert
VERIFY = os.getenv("AHORRATRON_VERIFY_SSL", "true").lower() in ("1", "true", "yes")


def main() -> int:
    if not USER or not PASSWORD:
        print("Missing CL_FALABELLA_USER / CL_FALABELLA_PASSWORD", file=sys.stderr)
        return 1

    # Multi-bank base64 format (explicit connector_id)
    client_id = base64.b64encode(
        json.dumps({"banco_falabella": USER}).encode()
    ).decode()
    client_secret = base64.b64encode(
        json.dumps({"banco_falabella": PASSWORD}).encode()
    ).decode()

    with httpx.Client(base_url=BASE, timeout=300.0, verify=VERIFY) as client:
        print(f"1. POST {BASE}/auth")
        r = client.post(
            "/auth", json={"clientId": client_id, "clientSecret": client_secret}
        )
        if r.status_code != 200:
            print(f"FAIL auth {r.status_code}: {r.text[:300]}", file=sys.stderr)
            return 2
        api_key = r.json()["apiKey"]
        headers = {"X-API-KEY": api_key}
        print("   auth OK")

        print("2. GET /accounts")
        r = client.get("/accounts", params={"itemId": "live-api"}, headers=headers)
        if r.status_code != 200:
            print(f"FAIL accounts {r.status_code}: {r.text[:300]}", file=sys.stderr)
            return 3
        accounts = r.json()
        results = accounts.get("results") or []
        print(f"   accounts={len(results)}")
        if len(results) < 2:
            print("FAIL: expected checking + CMR", file=sys.stderr)
            return 4

        ok_checking = ok_cmr = False
        for acc in results:
            aid = acc["id"]
            # Service may prefix connector_id:
            print(f"3. GET /v2/transactions accountId=…{aid[-8:]}")
            r = client.get(
                "/v2/transactions",
                params={"accountId": aid},
                headers=headers,
            )
            if r.status_code != 200:
                print(
                    f"FAIL txs {r.status_code}: {r.text[:300]}",
                    file=sys.stderr,
                )
                return 5
            txs = r.json().get("results") or []
            subtype = acc.get("subtype")
            print(f"   subtype={subtype} balance={acc.get('balance')} txs={len(txs)}")
            if subtype == "CHECKING_ACCOUNT" and txs:
                ok_checking = True
            if subtype == "CREDIT_CARD" and txs:
                ok_cmr = True

        if not ok_checking or not ok_cmr:
            print(
                f"FAIL: checking_ok={ok_checking} cmr_ok={ok_cmr}",
                file=sys.stderr,
            )
            return 6

    print("PASS: API auth + accounts + transactions (checking + CMR)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
