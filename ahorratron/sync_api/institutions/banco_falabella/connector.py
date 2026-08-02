"""Pluggy-compatible connector for Banco Falabella (checking + CMR)."""

from __future__ import annotations

import logging
from datetime import datetime

from cachetools import TTLCache

import ahorratron.sync_api.utils.constants as c
from ahorratron.sync_api.core.connector import ConnectorBase
from ahorratron.sync_api.institutions.banco_falabella.banco_falabella import (
    BancoFalabellaAPI,
)
from ahorratron.sync_api.institutions.banco_falabella.models import (
    MovementItem,
    MovementStatus,
    MovementTipo,
    ProductItem,
    ProductsResponse,
    ProductType,
)
from ahorratron.sync_api.models.account_models import (
    Account,
    AccountsResponse,
    AccountSubtype,
    AccountType,
    BankData,
    CreditData,
)
from ahorratron.sync_api.models.transaction_models import (
    Merchant,
    Transaction,
    TransactionsResponse,
    TransactionStatus,
    TransactionType,
)
from ahorratron.sync_api.utils.helpers import drop_none, to_utc

logger = logging.getLogger(__name__)


class BancoFalabellaConnector(ConnectorBase):
    def __init__(self, client: BancoFalabellaAPI):
        self._client = client
        self._cache = TTLCache[str, ProductsResponse](maxsize=100, ttl=60)

    def get_accounts(self, itemId: str) -> AccountsResponse:
        accounts = drop_none(
            [self._map_account(itemId, p) for p in self._productos.products]
        )
        return AccountsResponse(
            results=accounts,
            total=len(accounts),
            totalPages=1,
            page=1,
        )

    def get_account_by_id(self, accountId: str) -> Account:
        product = next(
            (p for p in self._productos.products if p.id == accountId), None
        )
        if not product:
            raise ValueError(f"Account with id {accountId} not found")
        mapped = self._map_account("not_needed_now", product)
        if mapped is None:
            raise ValueError(f"Error mapping account with id {accountId}")
        return mapped

    def get_transactions(self, accountId: str) -> TransactionsResponse:
        product = next(
            (p for p in self._productos.products if p.id == accountId), None
        )
        if not product:
            logger.warning("Account %s not found in productos", accountId)
            return TransactionsResponse()

        movements = self._client.get_movements(accountId)
        txs = [self._map_movement(m, product) for m in movements.movements]
        return TransactionsResponse(results=txs)

    @property
    def _productos(self) -> ProductsResponse:
        key = "productos"
        if key not in self._cache:
            logger.info("Fetching Falabella productos")
            self._cache[key] = self._client.get_products()
        else:
            logger.info("Using cached Falabella productos")
        return self._cache[key]

    def _map_account(self, itemId: str, product: ProductItem) -> Account | None:
        if product.type == ProductType.CHECKING:
            return Account(
                id=product.id,
                type=AccountType.BANK,
                subtype=AccountSubtype.CHECKING_ACCOUNT,
                number=product.number,
                name=product.name,
                currencyCode=c.CLP,
                itemId=itemId,
                # Actual UI labels BANK as "{name} - {taxNumber}"
                taxNumber=product.number,
                institution="Banco Falabella",
                balance=product.balance,
                bankData=BankData(
                    transferNumber=product.number,
                    closingBalance=product.balance,
                    automaticallyInvestedBalance=0,
                ),
            )
        if product.type == ProductType.CREDIT_CARD:
            return Account(
                id=product.id,
                type=AccountType.CREDIT,
                subtype=AccountSubtype.CREDIT_CARD,
                number=product.number,
                name=product.name,
                currencyCode=c.CLP,
                itemId=itemId,
                # Actual UI labels CREDIT as "{name} - {owner}"; null → "CMR - null"
                owner=product.number,
                institution="Banco Falabella",
                # Actual treats credit balance as debt (shows negative)
                balance=product.balance,
                creditLimit=product.credit_limit,
                availableBalance=product.available_credit,
                creditData=CreditData(
                    minimumPayment=None,
                    balanceForeignCurrency=None,
                    availableCreditLimit=product.available_credit,
                    creditLimit=product.credit_limit,
                    isLimitFlexible=None,
                    balanceDueDate=None,
                    balanceCloseDate=None,
                    level=None,
                    brand="CMR",
                    status=None,
                    holderType=None,
                ),
            )
        logger.warning("Unsupported Falabella product type: %s", product.type)
        return None

    def _map_movement(
        self, movement: MovementItem, product: ProductItem
    ) -> Transaction:
        # MovementItem is bank-cartola convention: cargo < 0, abono > 0.
        # Pluggy CREDIT (and Actual, which negates CREDIT amounts) expects the
        # opposite: purchase > 0, payment < 0 — same as Banco de Chile.
        if product.type == ProductType.CREDIT_CARD:
            amount = -movement.amount
            tx_type = (
                TransactionType.DEBIT if amount > 0 else TransactionType.CREDIT
            )
        elif movement.tipo == MovementTipo.CARGO:
            tx_type = TransactionType.DEBIT
            amount = movement.amount if movement.amount < 0 else -abs(movement.amount)
        else:
            tx_type = TransactionType.CREDIT
            amount = abs(movement.amount)

        status = (
            TransactionStatus.PENDING
            if movement.status == MovementStatus.PENDING
            else TransactionStatus.POSTED
        )
        when: datetime = to_utc(movement.datetime)
        return Transaction(
            id=movement.id,
            date=when,
            amount=amount,
            description=movement.description,
            accountId=product.id,
            type=tx_type,
            currencyCode=c.CLP,
            status=status,
            balance=movement.balance,
            merchant=Merchant(name=movement.description),
        )
