import logging

from .core.factory import get_connector
from .models.account_models import Account, AccountsResponse
from .models.core_models import UserData
from .models.transaction_models import TransactionsResponse

logger = logging.getLogger(__name__)

# Separator used to prefix account IDs with the connector name so that
# requests for a specific account can be routed to the right institution.
ACCOUNT_ID_SEP = ":"


class Service:
    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _prefix_id(connector_id: str, account_id: str) -> str:
        return f"{connector_id}{ACCOUNT_ID_SEP}{account_id}"

    @staticmethod
    def _parse_id(prefixed_id: str) -> tuple[str, str]:
        """Return ``(connector_id, original_id)``.

        Falls back to ``("", prefixed_id)`` for un-prefixed legacy IDs.
        """
        if ACCOUNT_ID_SEP in prefixed_id:
            connector_id, original = prefixed_id.split(ACCOUNT_ID_SEP, 1)
            return connector_id, original
        return "", prefixed_id

    def _find_user(
        self, users: list[UserData], prefixed_id: str
    ) -> tuple[UserData, str]:
        connector_id, original_id = self._parse_id(prefixed_id)
        if connector_id:
            for u in users:
                if u.connector_id == connector_id:
                    return u, original_id
            raise ValueError(f"No credentials for institution '{connector_id}'")
        # Legacy / single-bank: use the first (and only) user
        return users[0], prefixed_id

    # ── public API ──────────────────────────────────────────────────

    def get_accounts(self, users: list[UserData], itemId: str) -> AccountsResponse:
        all_accounts: list[Account] = []
        for user_data in users:
            connector = get_connector(user_data)
            try:
                response = connector.get_accounts(itemId=itemId)
            except Exception:
                logger.exception(
                    "Failed to get accounts for %s", user_data.connector_id
                )
                continue
            for account in response.results:
                account.id = self._prefix_id(user_data.connector_id, account.id)
            all_accounts.extend(response.results)

        return AccountsResponse(
            results=all_accounts,
            total=len(all_accounts),
            page=1,
            totalPages=1,
        )

    def get_account_by_id(self, users: list[UserData], accountId: str) -> Account:
        user_data, real_id = self._find_user(users, accountId)
        connector = get_connector(user_data)
        account = connector.get_account_by_id(accountId=real_id)
        account.id = self._prefix_id(user_data.connector_id, account.id)
        return account

    def get_transactions(
        self, users: list[UserData], accountId: str
    ) -> TransactionsResponse:
        user_data, real_id = self._find_user(users, accountId)
        connector = get_connector(user_data)
        return connector.get_transactions(accountId=real_id)
