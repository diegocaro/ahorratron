import hashlib
import logging

from ahorratron.sync_api.core.connector import ConnectorBase
from ahorratron.sync_api.institutions.banco_consorcio.banco_consorcio import (
    BancoConsorcioAPI,
)
from ahorratron.sync_api.institutions.banco_consorcio.connector import (
    BancoConsorcioConnector,
)
from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)
from ahorratron.sync_api.institutions.banco_de_chile.demo import DemoAPIClient
from ahorratron.sync_api.institutions.banco_falabella.banco_falabella import (
    BancoFalabellaAPI,
)
from ahorratron.sync_api.institutions.banco_falabella.connector import (
    BancoFalabellaConnector,
)
from ahorratron.sync_api.models.core_models import UserData

CONNECTORS = {
    "banco_de_chile": (BancoDeChileConnector, APIClient),
    "demo_banco_de_chile": (BancoDeChileConnector, DemoAPIClient),
    "banco_consorcio": (BancoConsorcioConnector, BancoConsorcioAPI),
    "banco_falabella": (BancoFalabellaConnector, BancoFalabellaAPI),
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
        connector_class, client_class = CONNECTORS[connector_id]
    except KeyError:
        raise ValueError(f"Connector '{connector_id}' not found.")

    client = client_class(user_data.clientId, user_data.clientSecret)
    return connector_class(client)


def get_connector(user_data: UserData) -> ConnectorBase:
    connector_id = user_data.connector_id
    try:
        connector_class, client_class = CONNECTORS[connector_id]
    except KeyError:
        raise ValueError(f"Connector '{connector_id}' not found.")

    # Always create a new connector if credentials changed (i.e., key not in cache)
    key = _make_key(user_data)
    if key not in _CONNECTOR_CACHE:
        logger.debug(
            f"Creating new connector for user {user_data.clientId} with key {key}"
        )
        client = client_class(user_data.clientId, user_data.clientSecret)
        _CONNECTOR_CACHE[key] = connector_class(client)
    return _CONNECTOR_CACHE[key]
