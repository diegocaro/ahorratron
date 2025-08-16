from .core.factory import get_connector
from .models.account_models import Account, AccountsResponse
from .models.core_models import UserData
from .models.transaction_models import TransactionsResponse


class Service:
    def get_account_by_id(self, user_data: UserData, accountId: str) -> Account:
        connector = get_connector(user_data)
        return connector.get_account_by_id(accountId=accountId)

    def get_accounts(self, user_data: UserData, itemId: str) -> AccountsResponse:
        connector = get_connector(user_data)
        return connector.get_accounts(itemId=itemId)

    def get_transactions(
        self, user_data: UserData, accountId: str
    ) -> TransactionsResponse:
        connector = get_connector(user_data)
        return connector.get_transactions(accountId=accountId)
