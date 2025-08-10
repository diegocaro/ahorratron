from ahorratron.sync_api.institutions.banco_de_chile.banco_de_chile import APIClient
from ahorratron.sync_api.institutions.banco_de_chile.connector import (
    BancoDeChileConnector,
)
from ahorratron.sync_api.institutions.banco_de_chile.demo import DemoAPIClient
from ahorratron.sync_api.models.core_models import UserData

CONNECTORS = {
    "banco_de_chile": (BancoDeChileConnector, APIClient),
    "demo_banco_de_chile": (BancoDeChileConnector, DemoAPIClient),
}


def get_connector(user_data: UserData) -> BancoDeChileConnector:

    connector_id = user_data.connector_id
    try:
        connector_class, client_class = CONNECTORS[connector_id]
    except KeyError:
        raise ValueError(f"Connector '{connector_id}' not found.")

    client = client_class()
    client.login(user_data.clientId, user_data.clientSecret)
    return connector_class(client)
