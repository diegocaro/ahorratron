from abc import ABC, abstractmethod

from ahorratron.sync_api.models.account_models import Account, AccountsResponse
from ahorratron.sync_api.models.transaction_models import TransactionsResponse


class ConnectorBase(ABC):
    @abstractmethod
    def get_accounts(self, itemId: str) -> AccountsResponse: ...

    @abstractmethod
    def get_account_by_id(self, accountId: str) -> Account: ...

    @abstractmethod
    def get_transactions(self, accountId: str) -> TransactionsResponse: ...
