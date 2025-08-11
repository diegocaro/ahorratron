from cachetools import TTLCache, cached

from ahorratron.sync_api.connectors import get_connector
from ahorratron.sync_api.models.account_models import Account, AccountsResponse
from ahorratron.sync_api.models.core_models import UserData
from ahorratron.sync_api.models.transaction_models import TransactionsResponse

CACHE_SIZE = 1000
CACHE_TTL_SECS = 300

account_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL_SECS)
accounts_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL_SECS)
transactions_cache = TTLCache(maxsize=CACHE_SIZE, ttl=CACHE_TTL_SECS)


@cached(account_cache)
def get_account_by_id_cached(user_data: UserData, accountId: str) -> Account:
    connector = get_connector(user_data)
    return connector.get_account_by_id(accountId=accountId)


@cached(accounts_cache)
def get_accounts_cached(user_data: UserData, itemId: str) -> AccountsResponse:
    connector = get_connector(user_data)
    return connector.get_accounts(itemId=itemId)


@cached(transactions_cache)
def get_transactions_cached(
    user_data: UserData, accountId: str
) -> TransactionsResponse:
    connector = get_connector(user_data)
    return connector.get_transactions(accountId=accountId)
