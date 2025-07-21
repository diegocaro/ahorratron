from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
from actual import Actual
from actual.queries import (
    create_transaction,
    get_account,
    get_accounts,
    get_budgets,
    get_transactions,
)

from .config import Settings, get_settings
from .models import Transaction


class ActualBudgetService:
    """
    Service class for interacting with Actual Budget.
    """

    def __init__(self, settings: Settings = get_settings()):
        self.base_url = settings.actual_url
        self.password = settings.actual_password
        self.file = settings.actual_file
        self.default_account = settings.actual_default_account
        self.payee_prefix = settings.payee_prefix

    def health_check(self) -> bool:
        with Actual(
            base_url=self.base_url, password=self.password, file=self.file
        ) as actual:
            get_accounts(actual.session)
            return True

    def _format_payee(self, payee: str) -> str:
        if not self.payee_prefix:
            return payee
        has_prefix = payee.lower().strip().startswith(self.payee_prefix.lower().strip())
        if not has_prefix:
            return f"{self.payee_prefix}{payee}"
        return payee

    def add_transaction(self, transaction: Transaction) -> str:
        with Actual(
            base_url=self.base_url, password=self.password, file=self.file
        ) as actual:
            account = get_account(actual.session, self.default_account)
            if not account:
                raise ValueError(f"Account {self.default_account} not found.")

            payee = self._format_payee(transaction.payee)

            t = create_transaction(
                actual.session,
                date=transaction.date.date(),
                account=account,
                payee=payee,
                notes=transaction.notes,
                amount=-transaction.amount,
            )
            actual.commit()
            return str(t.id)

    def get_summary(self, month: Optional[date] = None):
        with Actual(
            base_url=self.base_url, password=self.password, file=self.file
        ) as actual:
            if month is None:
                month = datetime.today().date()

            to_dataframe = lambda x: pd.DataFrame([r.model_dump() for r in x])

            budgets_raw = get_budgets(actual.session, month=month)
            budgets = to_dataframe(budgets_raw).rename(
                columns={"id": "budget_id", "amount": "budgeted"}
            )
            # Using this approach instead of `get_categories` to avoid fetching all transactions,
            # which is unnecessary here
            add_prefix = lambda x, prefix: {f"{prefix}_{k}": v for k, v in x.items()}
            categories_records = []
            for b in budgets_raw:
                category = add_prefix(b.category.model_dump(), "category")
                category_group = add_prefix(b.category.group.model_dump(), "group")
                categories_records.append({**category, **category_group})

            categories = pd.DataFrame(categories_records).rename(
                columns={"id": "category_id"}
            )

            transactions = to_dataframe(
                get_transactions(
                    actual.session,
                    start_date=month.replace(day=1),
                    end_date=(month.replace(day=1) + timedelta(days=31)).replace(day=1),
                )
            ).rename(columns={"id": "transaction_id"})

            spent = (
                transactions.groupby("category_id", as_index=False)
                .agg({"amount": "sum"})
                .rename(columns={"amount": "spent"})
            )

            joined = categories.merge(
                spent, on="category_id", how="left", validate="one_to_one"
            ).merge(budgets, on="category_id", how="left", validate="one_to_one")

            joined = joined[joined.category_is_income == False]  # noqa

            ans = joined[["category_name", "group_name", "budgeted", "spent"]].fillna(0)

            for col in ["budgeted", "spent"]:
                ans[col] = ans[col] / 100

            ans["spent"] = -ans["spent"]
            ans["available"] = ans["budgeted"] - ans["spent"]

            result = ans.to_dict(orient="records")
            return {"month": month.strftime("%Y-%m"), "categories": result}
