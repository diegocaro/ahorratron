import hashlib
import logging

from ahorratron.sync_api.core.connector import ConnectorBase
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)
from ahorratron.sync_api.institutions.banco_de_chile.demo import (
    BancoDeChileDemoConnector,
)
from ahorratron.sync_api.models.core_models import UserData

CONNECTORS = {
    "banco_de_chile": BancoDeChileConnector,
    "demo_banco_de_chile": BancoDeChileDemoConnector,
}

# Simple in-memory cache for connectors per user and institution
# You really need to use something like Redis or Memcached for production
_CONNECTOR_CACHE: dict[str, ConnectorBase] = {}

logger = logging.getLogger(__name__)


def _make_key(user_data: UserData) -> str:
    raw = f"{user_data.connector_id}:{user_data.clientId}:{user_data.clientSecret}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_connector_no_cache(user_data: UserData) -> ConnectorBase:
    connector_id = user_data.connector_id
    try:
        connector_class = CONNECTORS[connector_id]
    except KeyError:
        raise ValueError(f"Connector '{connector_id}' not found.")

    return connector_class.from_user_data(user_data)


def get_connector(user_data: UserData) -> ConnectorBase:
    connector_id = user_data.connector_id
    try:
        connector_class = CONNECTORS[connector_id]
    except KeyError:
        raise ValueError(f"Connector '{connector_id}' not found.")

    # Always create a new connector if credentials changed (i.e., key not in cache)
    key = _make_key(user_data)
    if key not in _CONNECTOR_CACHE:
        logger.debug(
            f"Creating new connector for user {user_data.clientId} with key {key}"
        )
        _CONNECTOR_CACHE[key] = connector_class.from_user_data(user_data)
    return _CONNECTOR_CACHE[key]
