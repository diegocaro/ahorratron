from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)

CONNECTORS = {"banco_de_chile": BancoDeChileConnector}


def get_connector(connector_id: str, **kwargs) -> BancoDeChileConnector:
    if connector_id not in CONNECTORS:
        raise ValueError(f"Connector {connector_id} not found")
    client = APIClient(**kwargs)
    return CONNECTORS[connector_id](client)
