"""Selenium client for Banco Falabella Chile — checking + CMR.

Login + DOM scrape (same UI path as fintself). CMR uses shadow DOM under
``credit-card-movements``; checking uses legacy ``#selectField_movimientos``.
"""

from __future__ import annotations

import hashlib
import logging
import os
import platform
import re
import time
from typing import Any

import selenium.common.exceptions as selenium_exceptions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ahorratron.sync_api.core.exceptions import LoginError
from ahorratron.sync_api.institutions.banco_falabella.models import (
    MovementItem,
    MovementsResponse,
    MovementStatus,
    MovementTipo,
    ProductItem,
    ProductsResponse,
    ProductType,
    currency_to_float,
)
from ahorratron.sync_api.utils.helpers import random_wait

logger = logging.getLogger(__name__)

BANK_LOGIN_URL = os.getenv("FALABELLA_LOGIN_URL", "https://www.bancofalabella.cl")
CMR_HOST = "credit-card-movements"
MAX_CMR_PAGES = 20
# How many MM/YYYY periods to scrape (newest first). Default 1 = current calendar month.
# "Últimos movimientos" / "Mes en curso" often leave the HTML table empty on this UI.
CHECKING_MAX_MONTHS = int(os.getenv("FALABELLA_CHECKING_MAX_MONTHS", "1"))

_CHECKING_TABLE_JS = """
() => {
    const results = [];
    const tables = Array.from(document.querySelectorAll("table"));
    for (const table of tables) {
        const rows = Array.from(table.querySelectorAll("tr"));
        if (rows.length < 2) continue;

        let dateIdx = 0, descIdx = 1, cargoIdx = -1, abonoIdx = -1,
            amountIdx = -1, balanceIdx = -1;
        let hasHeader = false;

        for (const row of rows) {
            const headers = row.querySelectorAll("th");
            if (headers.length < 2) continue;
            const hTexts = Array.from(headers).map(
                h => (h.innerText || "").trim().toLowerCase()
            );
            if (!hTexts.some(h => h.includes("fecha"))) continue;
            hasHeader = true;
            dateIdx = hTexts.findIndex(h => h.includes("fecha"));
            descIdx = hTexts.findIndex(
                h => h.includes("descrip") || h.includes("detalle") || h.includes("glosa")
            );
            cargoIdx = hTexts.findIndex(
                h => h.includes("cargo") || h.includes("débito") || h.includes("debito")
            );
            abonoIdx = hTexts.findIndex(
                h => h.includes("abono") || h.includes("crédito") || h.includes("credito")
            );
            amountIdx = hTexts.findIndex(h => h === "monto" || h.includes("importe"));
            balanceIdx = hTexts.findIndex(h => h.includes("saldo"));
            break;
        }
        if (!hasHeader) continue;

        let lastDate = "";
        for (const row of rows) {
            const cells = row.querySelectorAll("td");
            if (cells.length < 3) continue;
            const vals = Array.from(cells).map(c => (c.innerText || "").trim());
            const rawDate = vals[dateIdx] || "";
            const hasDate = /^\\d{1,2}[\\/.\\-]\\d{1,2}([\\/.\\-]\\d{2,4})?$/.test(rawDate);
            const date = hasDate ? rawDate : lastDate;
            if (!date) continue;
            if (hasDate) lastDate = rawDate;

            const description = descIdx >= 0 ? (vals[descIdx] || "") : "";
            let amountStr = "";
            let tipo = "";
            if (cargoIdx >= 0 && vals[cargoIdx] && vals[cargoIdx].replace(/\\s/g, "")) {
                amountStr = vals[cargoIdx];
                tipo = "cargo";
            } else if (abonoIdx >= 0 && vals[abonoIdx] && vals[abonoIdx].replace(/\\s/g, "")) {
                amountStr = vals[abonoIdx];
                tipo = "abono";
            } else if (amountIdx >= 0) {
                amountStr = vals[amountIdx] || "";
                tipo = amountStr.trim().startsWith("-") ? "cargo" : "abono";
            }
            if (!amountStr) continue;

            results.push({
                date,
                description,
                amount_str: amountStr,
                balance_str: balanceIdx >= 0 ? (vals[balanceIdx] || "") : "",
                tipo,
            });
        }
    }
    return results;
}
"""

_PRODUCTS_JS = """
() => {
    const out = [];
    const debug = {
        accountDetail0: !!document.querySelector("#accountDetail0"),
        cardDetail0: !!document.querySelector("#cardDetail0"),
        divProducts: document.querySelectorAll("a.div-product").length,
        title: (document.querySelector("label.title-products") || {}).innerText || "",
    };

    for (const acct of Array.from(document.querySelectorAll(
        "#accountDetail0, a.div-product[id^='accountDetail']"
    ))) {
        const t = (acct.innerText || "").replace(/\\s+/g, " ").trim();
        const digits = (t.match(/\\d[\\d\\s]+\\d/) || [""])[0].replace(/\\D/g, "");
        let balance = "";
        const row = acct.closest(".grid-container") || acct.parentElement;
        if (row) {
            const green = row.querySelector(".green-text-bold");
            if (green) balance = (green.innerText || "").trim();
        }
        if (digits.length >= 4) {
            out.push({
                id: digits,
                name: "Cuenta Corriente",
                number: digits,
                type: "checking",
                balance_str: balance,
            });
            break;
        }
    }

    for (const card of Array.from(document.querySelectorAll(
        "#cardDetail0, app-credit-cards a.div-product, a.div-product[id^='cardDetail']"
    ))) {
        const t = (card.innerText || "").replace(/\\s+/g, " ").trim();
        const last4 = (
            t.match(/[•·*]\\s*(\\d{4})\\s*$/)
            || t.match(/(\\d{4})\\s*$/)
            || []
        )[1];
        const row = card.closest(".grid-container") || card.parentElement;
        let used = "", limit = "", avail = "";
        if (row) {
            const blocks = Array.from(row.querySelectorAll(".div-content"));
            for (const el of blocks) {
                const v = ((el.querySelector("div") || el).innerText || "").trim();
                const l = ((el.querySelector("span") || {}).innerText || "").toLowerCase();
                if (l.includes("utilizado")) used = v;
                else if (l.includes("cupo de compras")) limit = v;
                else if (l.includes("disponible") && (l.includes("cupo") || l.includes("monto"))) avail = v;
            }
            if (!used) {
                const amounts = Array.from(row.querySelectorAll(".darker, .green-text-bold"))
                    .map(e => (e.innerText || "").trim())
                    .filter(x => x.includes("$"));
                if (amounts.length >= 2) { limit = amounts[0]; used = amounts[1]; }
                if (amounts.length >= 3) avail = amounts[2];
            }
        }
        if (last4) {
            out.push({
                id: last4,
                name: "CMR",
                number: last4,
                type: "credit_card",
                balance_str: used,
                limit_str: limit,
                available_str: avail,
            });
            break;
        }
    }

    return { products: out, debug };
}
"""

# Ported from fintself falabella._CMR_PAGE_JS
_CMR_PAGE_JS = """
({ host, isBilled }) => {
    const shadowEl = document.querySelector(host);
    const topRoot = (shadowEl && shadowEl.shadowRoot) || document;

    function collect(root) {
        const found = root === document ? [] : [root];
        const base = root === document ? document : root;
        for (const el of Array.from(base.querySelectorAll("*"))) {
            if (el.shadowRoot) found.push(...collect(el.shadowRoot));
        }
        return found;
    }
    const roots = collect(topRoot);

    const allTables = roots.flatMap(r => Array.from(r.querySelectorAll("table")));
    function isVisible(t) {
        const rect = t.getBoundingClientRect();
        return rect.width > 0 || rect.height > 0;
    }

    let tablesToUse = isBilled
        ? allTables.filter(t => {
            if (!isVisible(t)) return false;
            const hdr = (
                (t.querySelector("thead, tr:first-child") || {}).innerText || ""
            ).toLowerCase();
            return (
                hdr.includes("fecha de compra")
                || hdr.includes("monto total")
                || hdr.includes("cuota a pagar")
            );
        })
        : allTables.filter(t => isVisible(t));

    if (tablesToUse.length === 0) {
        tablesToUse = allTables.filter(
            t => isVisible(t) && !t.closest("app-last-movements")
        );
    }

    const rows = [];
    for (const table of tablesToUse) {
        for (const row of Array.from(table.querySelectorAll("tbody tr"))) {
            const cells = row.querySelectorAll("td");
            if (cells.length < 4) continue;
            const texts = Array.from(cells).map(c => (c.innerText || "").trim());
            const dateMatch = (texts[0] || "").match(/(\\d{1,2}\\/\\d{1,2}\\/\\d{2,4})/);
            const pendingImg = row.querySelector(
                "td:first-child img[alt*='pendiente'], td:first-child .td-time-img"
            );
            if (!dateMatch && !pendingImg && texts[0] !== "") continue;
            const date = dateMatch ? dateMatch[1] : "";
            const description = texts[1] || "";
            const totalText = texts[3] || "";
            const cuotaText = texts[5] || "";
            const montoText = cuotaText || totalText;
            const isNeg = montoText.includes("-$");
            const amountMatch = montoText.match(/\\$\\s*([\\d.,]+)/);
            let amountStr = "";
            if (amountMatch) {
                amountStr = (isNeg ? "" : "-") + amountMatch[1];
            }
            if (description && amountStr) {
                rows.push({
                    date,
                    description,
                    amount_str: amountStr,
                    owner: texts[2] || "",
                    installments: texts[4] || "",
                });
            }
        }
    }

    let firstRow = "";
    for (const r of roots) {
        const cells = r.querySelectorAll("table tbody tr:first-child td");
        if (cells.length > 0) {
            firstRow = Array.from(cells).map(c => (c.innerText || "").trim()).join("|");
            break;
        }
    }

    let clicked = false;
    for (const root of roots) {
        if (clicked) break;
        for (const btn of Array.from(root.querySelectorAll(".btn-pagination, button"))) {
            if (btn.disabled) continue;
            const img = btn.querySelector("img");
            const imgAlt = ((img && img.getAttribute("alt")) || "").toLowerCase();
            const imgSrc = (img && img.getAttribute("src")) || "";
            const label = (
                btn.getAttribute("aria-label") || btn.innerText || ""
            ).toLowerCase();
            const isNext =
                imgAlt.includes("avanzar")
                || imgAlt.includes("siguiente")
                || imgAlt.includes("next")
                || imgSrc.includes("right-arrow")
                || imgSrc.includes("arrow-right")
                || imgSrc.includes("next")
                || label.includes("siguiente")
                || label.includes("next")
                || label.includes("avanzar");
            if (isNext) {
                btn.click();
                clicked = true;
                break;
            }
        }
    }

    return { rows, firstRow, clicked };
}
"""

_CMR_BILLED_TAB_JS = """
({ host, radioId }) => {
    const shadowEl = document.querySelector(host);
    const roots = [];
    if (shadowEl && shadowEl.shadowRoot) roots.push(shadowEl.shadowRoot);
    roots.push(document);

    for (const root of roots) {
        const radio = root.querySelector("#" + radioId);
        if (radio) {
            radio.checked = true;
            radio.dispatchEvent(new Event("change", { bubbles: true }));
            radio.click();
            const label = root.querySelector('label[for="' + radio.id + '"]')
                || radio.closest("label");
            if (label) label.click();
            return true;
        }
    }
    for (const root of roots) {
        for (const label of Array.from(root.querySelectorAll("label"))) {
            if (!(label.innerText || "").toLowerCase().includes("facturado")) continue;
            const forId = label.getAttribute("for");
            const radio = forId
                ? root.querySelector("#" + forId)
                : label.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
                radio.dispatchEvent(new Event("change", { bubbles: true }));
                radio.click();
            }
            label.click();
            return true;
        }
    }
    return false;
}
"""


class BancoFalabellaAPI:
    TIMEOUT_SECONDS = 45

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._products: ProductsResponse | None = None
        self._movements: dict[str, MovementsResponse] = {}
        self._dashboard_url: str | None = None

    def get_products(self) -> ProductsResponse:
        self._ensure_scraped()
        assert self._products is not None
        return self._products

    def get_movements(self, account_id: str) -> MovementsResponse:
        self._ensure_scraped()
        if account_id not in self._movements:
            logger.warning("No movements cached for account %s", account_id)
            return MovementsResponse(account_id=account_id, movements=[])
        return self._movements[account_id]

    def _ensure_scraped(self) -> None:
        if self._products is not None:
            return
        logger.info("Scraping Banco Falabella session for %s", self._username)
        driver = self._make_driver()
        try:
            self._login(driver)
            self._dashboard_url = driver.current_url
            products = self._scrape_products(driver)
            self._products = ProductsResponse(products=products)

            # Checking first while consolidada is fresh, then back() for CMR.
            for product in products:
                if product.type == ProductType.CHECKING:
                    self._movements[product.id] = self._scrape_checking_movements(
                        driver, product
                    )

            if any(p.type == ProductType.CREDIT_CARD for p in products):
                self._go_to_dashboard(driver)
                for product in products:
                    if product.type == ProductType.CREDIT_CARD:
                        self._movements[product.id] = self._scrape_cmr_movements(
                            driver, product
                        )
        finally:
            driver.quit()

    def _make_driver(self) -> webdriver.Chrome | webdriver.Remote:
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1366,900")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        if platform.system().lower() == "linux":
            return webdriver.Remote(
                command_executor="http://selenium:4444/wd/hub", options=chrome_options
            )
        return webdriver.Chrome(options=chrome_options)

    def _login(self, driver: webdriver.Chrome | webdriver.Remote) -> None:
        wait = WebDriverWait(driver, self.TIMEOUT_SECONDS)
        try:
            driver.get(BANK_LOGIN_URL)
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#main-header__sub-content, #btn-auth-normal")
                )
            )
        except Exception as e:
            raise ValueError(f"Error loading Falabella homepage: {e}") from e

        if not self._click_mi_cuenta(driver):
            raise LoginError("Could not find 'Mi cuenta' on Banco Falabella homepage.")

        random_wait(1, 2)
        try:
            rut = wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        'input[name*="rut"], input[id*="rut"], input[placeholder*="RUT"]',
                    )
                )
            )
            rut.clear()
            rut.send_keys(self._username)
            rut.send_keys(Keys.ENTER)
            random_wait(1, 2)
            pwd = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'input[type="password"]')
                )
            )
            pwd.clear()
            pwd.send_keys(self._password)
            try:
                driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
            except selenium_exceptions.NoSuchElementException:
                pwd.send_keys(Keys.ENTER)
            wait.until(EC.presence_of_element_located((By.ID, "accountDetail0")))
        except selenium_exceptions.TimeoutException as e:
            raise LoginError(
                "Login timed out — check credentials or Falabella UI changes"
            ) from e

        self._dismiss_marketing(driver)
        logger.info("Falabella login OK")

    def _click_mi_cuenta(self, driver: webdriver.Chrome | webdriver.Remote) -> bool:
        selectors = [
            "#btn-auth-normal",
            "#main-header__sub-content button",
        ]
        for sel in selectors:
            try:
                els = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in els:
                    text = (el.text or "").strip().lower()
                    if sel == "#btn-auth-normal" or "mi cuenta" in text:
                        el.click()
                        return True
            except (
                selenium_exceptions.ElementClickInterceptedException,
                selenium_exceptions.StaleElementReferenceException,
                selenium_exceptions.WebDriverException,
            ) as e:
                logger.debug("Mi cuenta click via %s failed: %s", sel, e)
                continue
        clicked = driver.execute_script(
            """
            const btn = document.querySelector('#btn-auth-normal')
              || Array.from(document.querySelectorAll('button'))
                   .find(b => /mi cuenta/i.test(b.innerText || ''));
            if (btn) { btn.click(); return true; }
            return false;
            """
        )
        return bool(clicked)

    def _dismiss_marketing(self, driver: webdriver.Chrome | webdriver.Remote) -> None:
        try:
            driver.execute_script(
                """
                const shadow = document.querySelector('#background-shadow');
                if (shadow) {
                    shadow.classList.remove('visible');
                    shadow.style.display = 'none';
                    shadow.style.pointerEvents = 'none';
                }
                """
            )
        except selenium_exceptions.WebDriverException as e:
            logger.debug("dismiss marketing skipped: %s", e)

    def _has_dashboard_products(
        self, driver: webdriver.Chrome | webdriver.Remote
    ) -> bool:
        try:
            return bool(
                driver.execute_script(
                    "return !!(document.querySelector('#accountDetail0')"
                    " || document.querySelector('#cardDetail0')"
                    " || document.querySelector('app-credit-cards'));"
                )
            )
        except selenium_exceptions.WebDriverException:
            return False

    def _go_to_dashboard(self, driver: webdriver.Chrome | webdriver.Remote) -> None:
        logger.info("Returning to Falabella dashboard")
        # Prefer history back (keeps SPA state); fallback to stored URL / home click.
        for attempt in ("back", "url", "home_click"):
            try:
                if attempt == "back":
                    driver.back()
                elif attempt == "url" and self._dashboard_url:
                    driver.get(self._dashboard_url)
                else:
                    driver.execute_script(
                        """
                        const els = Array.from(document.querySelectorAll('a,button'));
                        const home = els.find(el => {
                          const t = ((el.innerText || '') + ' '
                            + (el.getAttribute('aria-label') || '')
                            + ' ' + (el.getAttribute('title') || '')).toLowerCase();
                          return /inicio|home|mis productos|consolidada/.test(t);
                        });
                        if (home) home.click();
                        """
                    )
            except selenium_exceptions.WebDriverException as e:
                logger.debug("dashboard return via %s failed: %s", attempt, e)
            random_wait(2, 4)
            self._dismiss_marketing(driver)
            if self._has_dashboard_products(driver):
                logger.info("Dashboard restored via %s", attempt)
                return
            try:
                WebDriverWait(driver, 8).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "#accountDetail0, #cardDetail0, app-credit-cards",
                        )
                    )
                )
                logger.info("Dashboard restored via %s (wait)", attempt)
                return
            except selenium_exceptions.TimeoutException:
                continue
        logger.warning(
            "Dashboard products not visible after return (url=%s)",
            driver.current_url[:120],
        )

    def _scrape_products(
        self, driver: webdriver.Chrome | webdriver.Remote
    ) -> list[ProductItem]:
        self._dismiss_marketing(driver)
        # Angular consolidada can lag a beat after #accountDetail0 appears
        random_wait(2, 3)
        payload = driver.execute_script("return (" + _PRODUCTS_JS + ")();") or {}
        if isinstance(payload, list):
            raw = payload
            debug = {}
        else:
            raw = payload.get("products") or []
            debug = payload.get("debug") or {}
        if not raw:
            logger.warning(
                "No products parsed (debug=%s url=%s)",
                debug,
                driver.current_url[:120],
            )
        products: list[ProductItem] = []
        for item in raw:
            ptype = (
                ProductType.CREDIT_CARD
                if item.get("type") == "credit_card"
                else ProductType.CHECKING
            )
            bal = currency_to_float(str(item.get("balance_str") or "0")) or 0.0
            products.append(
                ProductItem(
                    id=str(item["id"]),
                    name=str(item.get("name") or "Cuenta"),
                    number=str(item.get("number") or item["id"]),
                    type=ptype,
                    balance=bal,
                    credit_limit=currency_to_float(
                        str(item.get("limit_str") or "") or None
                    ),
                    available_credit=currency_to_float(
                        str(item.get("available_str") or "") or None
                    ),
                )
            )
        logger.info(
            "Falabella products: %s",
            [(p.type.value, p.id, p.balance) for p in products],
        )
        return products

    def _scrape_checking_movements(
        self,
        driver: webdriver.Chrome | webdriver.Remote,
        product: ProductItem,
    ) -> MovementsResponse:
        wait = WebDriverWait(driver, self.TIMEOUT_SECONDS)
        self._dismiss_marketing(driver)
        driver.execute_script("document.querySelector('#accountDetail0')?.click()")
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#selectField_movimientos, table")
                )
            )
        except selenium_exceptions.TimeoutException:
            logger.warning("Checking movements UI did not appear for %s", product.id)
            return MovementsResponse(account_id=product.id, movements=[])

        random_wait(2, 3)
        periods = self._checking_period_options(driver)
        if not periods:
            logger.info("No period select — scraping default checking table only")
            rows = self._read_checking_table_pages(driver)
            return MovementsResponse(
                account_id=product.id,
                movements=self._rows_to_checking_movements(rows, product.id),
            )

        all_rows: list[dict[str, Any]] = []
        for value, label in periods:
            logger.info("Checking period: %s (%s)", label, value)
            if not self._select_checking_period(driver, value):
                logger.warning("Could not select checking period %s", label)
                continue
            random_wait(2, 4)
            period_rows = self._read_checking_table_pages(driver)
            logger.info("  → %d raw rows", len(period_rows))
            all_rows.extend(period_rows)

        movements = self._rows_to_checking_movements(all_rows, product.id)
        logger.info(
            "Falabella checking %s: %d movements across %d periods",
            product.id,
            len(movements),
            len(periods),
        )
        return MovementsResponse(account_id=product.id, movements=movements)

    def _checking_period_options(
        self, driver: webdriver.Chrome | webdriver.Remote
    ) -> list[tuple[str, str]]:
        """Recent movements only by default (+ optional historic MM/YYYY)."""
        try:
            el = driver.find_element(By.ID, "selectField_movimientos")
        except selenium_exceptions.NoSuchElementException:
            return []

        options = [
            (
                (opt.get_attribute("value") or "").strip(),
                (opt.text or "").strip(),
            )
            for opt in Select(el).options
        ]
        return self._pick_checking_periods(options, CHECKING_MAX_MONTHS)

    @staticmethod
    def _pick_checking_periods(
        options: list[tuple[str, str]], max_months: int
    ) -> list[tuple[str, str]]:
        """Newest MM/YYYY month(s). Skip Últimos/Mes en curso (empty DOM tables)."""
        months: list[tuple[str, str]] = []
        for value, label in options:
            if not value:
                continue
            if re.match(r"^\d{2}/\d{4}$", value) or re.match(r"^\d{2}/\d{4}$", label):
                months.append((value, label or value))
        n = max_months if max_months > 0 else 1
        return months[:n]

    def _select_checking_period(
        self, driver: webdriver.Chrome | webdriver.Remote, value: str
    ) -> bool:
        try:
            el = driver.find_element(By.ID, "selectField_movimientos")
            Select(el).select_by_value(value)
            # Legacy onchange sometimes needs an explicit event
            driver.execute_script(
                """
                const s = document.getElementById('selectField_movimientos');
                if (!s) return;
                s.dispatchEvent(new Event('change', { bubbles: true }));
                if (typeof s.onchange === 'function') s.onchange();
                """
            )
            return True
        except (
            selenium_exceptions.NoSuchElementException,
            selenium_exceptions.UnexpectedTagNameException,
            selenium_exceptions.WebDriverException,
        ) as e:
            logger.debug("select period %s failed: %s", value, e)
            return False

    def _read_checking_table_pages(
        self, driver: webdriver.Chrome | webdriver.Remote
    ) -> list[dict[str, Any]]:
        """Parse current table; click 'siguiente' / 'ver más' if present."""
        rows: list[dict[str, Any]] = []
        seen_sig: set[str] = set()
        for _ in range(20):
            page_rows: list[dict[str, Any]] = (
                driver.execute_script("return (" + _CHECKING_TABLE_JS + ")();") or []
            )
            sig = "|".join(
                f"{r.get('date')}:{r.get('description')}:{r.get('amount_str')}"
                for r in page_rows[:3]
            )
            if sig and sig in seen_sig:
                break
            if sig:
                seen_sig.add(sig)
            rows.extend(page_rows)
            if not self._click_checking_next_page(driver):
                break
            random_wait(1.5, 2.5)
        return rows

    def _click_checking_next_page(
        self, driver: webdriver.Chrome | webdriver.Remote
    ) -> bool:
        return bool(
            driver.execute_script(
                """
                const buttons = Array.from(document.querySelectorAll('button, a'));
                for (const btn of buttons) {
                  if (btn.disabled) continue;
                  const t = (btn.innerText || btn.getAttribute('aria-label') || '')
                    .toLowerCase().trim();
                  if (/siguiente|ver más|ver mas|mostrar más|mostrar mas/.test(t)) {
                    btn.click();
                    return true;
                  }
                }
                return false;
                """
            )
        )

    def _rows_to_checking_movements(
        self, raw_rows: list[dict[str, Any]], account_id: str
    ) -> list[MovementItem]:
        movements: list[MovementItem] = []
        seen: set[str] = set()
        for row in raw_rows:
            amount = currency_to_float(str(row.get("amount_str") or ""))
            if amount is None:
                continue
            tipo_raw = (row.get("tipo") or "").lower()
            if tipo_raw == "cargo":
                tipo = MovementTipo.CARGO
                if amount > 0:
                    amount = -amount
            else:
                tipo = MovementTipo.ABONO
                amount = abs(amount)

            date = self._normalize_date(str(row.get("date") or ""))
            if not date:
                continue
            desc = str(row.get("description") or "").strip()
            bal = currency_to_float(str(row.get("balance_str") or "") or None)
            mid = hashlib.sha1(
                f"{account_id}|{date}|{desc}|{amount}".encode()
            ).hexdigest()[:24]
            if mid in seen:
                continue
            seen.add(mid)
            movements.append(
                MovementItem(
                    id=mid,
                    date=date,
                    description=desc or "Movimiento",
                    amount=amount,
                    balance=bal,
                    tipo=tipo,
                    status=MovementStatus.POSTED,
                )
            )
        logger.info("Falabella checking %s: %d movements", account_id, len(movements))
        return movements

    def _scrape_cmr_movements(
        self,
        driver: webdriver.Chrome | webdriver.Remote,
        product: ProductItem,
    ) -> MovementsResponse:
        self._dismiss_marketing(driver)
        opened = driver.execute_script(
            """
            const el = document.querySelector('#cardDetail0')
                || document.querySelector("a.div-product[id^='cardDetail']")
                || document.querySelector('app-credit-cards a.div-product')
                || document.querySelector('#cardAccount0');
            if (!el) return false;
            el.scrollIntoView({block:'center'});
            el.click();
            return true;
            """
        )
        if not opened:
            logger.warning("CMR card not found on dashboard")
            return MovementsResponse(account_id=product.id, movements=[])

        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, CMR_HOST))
            )
            logger.info("CMR host %s present", CMR_HOST)
        except selenium_exceptions.TimeoutException:
            # Host tag may differ; still try tables / log tags
            tags = driver.execute_script(
                """
                return Array.from(document.querySelectorAll('*'))
                  .map(e => e.tagName.toLowerCase())
                  .filter(t => t.includes('credit') || t.includes('card') || t.includes('movement'))
                  .slice(0, 40);
                """
            )
            logger.warning(
                "CMR host %s not found; credit-ish tags=%s url=%s",
                CMR_HOST,
                tags,
                driver.current_url[:120],
            )
        random_wait(3, 5)
        self._wait_for_cmr_tables(driver)

        unbilled = self._paginate_cmr(
            driver, product.id, billed=False, status=MovementStatus.PENDING
        )
        if self._click_cmr_billed_tab(driver):
            random_wait(2, 3)
            self._wait_for_cmr_tables(driver)
            billed = self._paginate_cmr(
                driver,
                product.id,
                billed=True,
                status=MovementStatus.POSTED,
                last_month_only=True,
            )
        else:
            logger.warning("Could not open CMR billed tab")
            billed = []

        # Dedup: drop pending whose date <= max billed (BdC pattern)
        movements = self._dedupe_cmr(billed, unbilled)
        logger.info(
            "Falabella CMR %s: %d movements (%d billed last-month + %d unbilled raw)",
            product.id,
            len(movements),
            len(billed),
            len(unbilled),
        )
        return MovementsResponse(account_id=product.id, movements=movements)

    def _wait_for_cmr_tables(self, driver: webdriver.Chrome | webdriver.Remote) -> None:
        deadline = time.time() + 30
        while time.time() < deadline:
            ok = driver.execute_script(
                f"""
                const host = "{CMR_HOST}";
                const el = document.querySelector(host);
                if (!el || !el.shadowRoot) return false;
                function collect(root) {{
                    const found = [root];
                    for (const child of Array.from(root.querySelectorAll("*"))) {{
                        if (child.shadowRoot) found.push(...collect(child.shadowRoot));
                    }}
                    return found;
                }}
                return collect(el.shadowRoot).some(
                    r => r.querySelectorAll("table tbody tr td").length > 0
                );
                """
            )
            if ok:
                return
            time.sleep(0.5)
        logger.warning("Timeout waiting for CMR shadow DOM tables")

    def _click_cmr_billed_tab(
        self, driver: webdriver.Chrome | webdriver.Remote
    ) -> bool:
        return bool(
            driver.execute_script(
                "return (" + _CMR_BILLED_TAB_JS + ")(arguments[0]);",
                {"host": CMR_HOST, "radioId": "invoicedMovements"},
            )
        )

    def _paginate_cmr(
        self,
        driver: webdriver.Chrome | webdriver.Remote,
        account_id: str,
        *,
        billed: bool,
        status: MovementStatus,
        last_month_only: bool = False,
    ) -> list[MovementItem]:
        all_movs: list[MovementItem] = []
        seen: set[str] = set()
        target_ym: tuple[int, int] | None = None
        for _ in range(MAX_CMR_PAGES):
            result = driver.execute_script(
                "return (" + _CMR_PAGE_JS + ")(arguments[0]);",
                {"host": CMR_HOST, "isBilled": billed},
            ) or {"rows": [], "clicked": False}
            page_movs: list[MovementItem] = []
            for row in result.get("rows") or []:
                mov = self._row_to_cmr_movement(row, account_id, status)
                if not mov or mov.id in seen:
                    continue
                seen.add(mov.id)
                page_movs.append(mov)
            if last_month_only:
                if target_ym is None and page_movs:
                    newest = max(m.datetime for m in page_movs)
                    target_ym = (newest.year, newest.month)
                kept = [
                    m
                    for m in page_movs
                    if target_ym
                    and (m.datetime.year, m.datetime.month) == target_ym
                ]
                all_movs.extend(kept)
                # Left the newest statement month — stop paging.
                if target_ym and page_movs and not kept:
                    break
            else:
                all_movs.extend(page_movs)
            if not result.get("clicked"):
                break
            time.sleep(1.2)
        return all_movs

    def _row_to_cmr_movement(
        self,
        row: dict[str, Any],
        account_id: str,
        status: MovementStatus,
    ) -> MovementItem | None:
        date = self._normalize_date(str(row.get("date") or "").replace("-", "/"))
        if not date:
            return None
        desc = str(row.get("description") or "").strip()
        amount = currency_to_float(str(row.get("amount_str") or ""))
        if not desc or amount is None or amount == 0:
            return None
        cuota = self._format_installments(str(row.get("installments") or ""))
        if cuota and not desc.endswith(cuota):
            desc = f"{desc} {cuota}"
        # JS emits bank convention: purchase negative, payment positive (UI "-$").
        tipo = MovementTipo.ABONO if amount > 0 else MovementTipo.CARGO
        mid = hashlib.sha1(
            f"{account_id}|{date}|{desc}|{amount}|{status.value}".encode()
        ).hexdigest()[:24]
        return MovementItem(
            id=mid,
            date=date,
            description=desc,
            amount=amount,
            tipo=tipo,
            status=status,
        )

    @staticmethod
    def _format_installments(raw: str) -> str | None:
        """Normalize '1/12', '01 / 12', '1 de 12' → '01/12' for the description."""
        m = re.search(r"(\d+)\s*(?:/|de)\s*(\d+)", raw.strip(), re.IGNORECASE)
        if not m:
            return None
        cur, total = int(m.group(1)), int(m.group(2))
        if cur < 1 or total < 2 or cur > total:
            return None  # skip 1/1 noise; only real multi-cuota
        width = max(2, len(str(total)))
        return f"{cur:0{width}d}/{total:0{width}d}"

    @staticmethod
    def _dedupe_cmr(
        billed: list[MovementItem], unbilled: list[MovementItem]
    ) -> list[MovementItem]:
        if not billed:
            return billed + unbilled
        max_billed = max(m.datetime for m in billed)
        kept_pending = [m for m in unbilled if m.datetime > max_billed]
        return billed + kept_pending

    @staticmethod
    def _normalize_date(raw: str) -> str | None:
        raw = raw.strip()
        m = re.match(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$", raw)
        if not m:
            return None
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        return f"{d:02d}/{mo:02d}/{y:04d}"
