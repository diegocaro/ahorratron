import decimal
from typing import Optional

from actual import Actual
from actual.queries import create_transaction, get_account, get_accounts

from .config import settings
from .models import Transaction


class ActualBudgetService:
    """
    Service class for interacting with Actual Budget.
    """

    def __init__(self):
        self.base_url = settings.actual_url
        self.password = settings.actual_password
        self.file = settings.actual_file
        self.default_account = settings.actual_default_account

    def health_check(self) -> bool:

        with Actual(
            base_url=self.base_url, password=self.password, file=self.file
        ) as actual:
            get_accounts(actual.session)
            return True

    def add_transaction(self, transaction: Transaction) -> str:
        with Actual(
            base_url=self.base_url, password=self.password, file=self.file
        ) as actual:
            account = get_account(actual.session, transaction.account)
            t = create_transaction(
                actual.session,
                transaction.date.date(),
                account,
                transaction.payee or "Unknown",
                notes=transaction.notes or "",
                amount=decimal.Decimal(transaction.amount),
            )
            actual.commit()
            return str(t.id)

    def get_transactions(self, account: Optional[str] = None):
        if account is None:
            account = self.default_account
        with Actual(
            base_url=self.base_url, password=self.password, file=self.file
        ) as actual:
            account = get_account(actual.session, account)

            return [
                {
                    "id": t.id,
                    "date": t.get_date(),
                    "payee": t.payee.name if t.payee else None,
                    "category": t.category.name if t.category else None,
                    "notes": t.notes,
                    "amount": (float(t.get_amount())),
                    "account": t.account.name,
                }
                # {k: v for k, v in t.__dict__.items() if not k.startswith("_sa_")}
                for t in account.transactions
            ]
