from fastapi import BackgroundTasks

from .connectors import get_connector
from .models.account_models import Account, AccountsResponse
from .models.core_models import UserData
from .models.transaction_models import TransactionsResponse
from .utils.cache import BackgroundRefreshCache, cache_with_background

CACHE_SIZE = 1000
CACHE_TTL_SECONDS = 300

CACHE = BackgroundRefreshCache(ttl_seconds=CACHE_TTL_SECONDS)


class Service:
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    @cache_with_background(CACHE)
    def get_account_by_id(self, user_data: UserData, accountId: str) -> Account:
        connector = get_connector(user_data)
        return connector.get_account_by_id(accountId=accountId)

    @cache_with_background(CACHE)
    def get_accounts(self, user_data: UserData, itemId: str) -> AccountsResponse:
        connector = get_connector(user_data)
        return connector.get_accounts(itemId=itemId)

    @cache_with_background(CACHE)
    def get_transactions(
        self, user_data: UserData, accountId: str
    ) -> TransactionsResponse:
        connector = get_connector(user_data)
        return connector.get_transactions(accountId=accountId)
