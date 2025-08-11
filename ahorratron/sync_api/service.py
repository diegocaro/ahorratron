from functools import lru_cache

from ahorratron.sync_api.connectors import get_connector
from ahorratron.sync_api.models.account_models import Account, AccountsResponse
from ahorratron.sync_api.models.core_models import UserData
from ahorratron.sync_api.models.transaction_models import TransactionsResponse


@lru_cache(maxsize=1000)
def get_account_by_id_cached(user_data: UserData, accountId: str) -> Account:
    connector = get_connector(user_data)
    return connector.get_account_by_id(accountId=accountId)


@lru_cache(maxsize=1000)
def get_accounts_cached(user_data: UserData, itemId: str) -> AccountsResponse:
    connector = get_connector(user_data)
    return connector.get_accounts(itemId=itemId)


@lru_cache(maxsize=1000)
def get_transactions_cached(
    user_data: UserData, accountId: str
) -> TransactionsResponse:
    connector = get_connector(user_data)
    return connector.get_transactions(accountId=accountId)
