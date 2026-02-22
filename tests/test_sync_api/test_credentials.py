import base64
import json

import pytest

from ahorratron.sync_api.core.credentials import (
    CredentialError,
    parse_multi_credentials,
)


def _b64(obj: dict) -> str:
    return base64.b64encode(json.dumps(obj).encode()).decode()


class TestMultiBankFormat:
    def test_two_institutions(self):
        ids = _b64({"banco_de_chile": "11111111-1", "banco_consorcio": "22222222-2"})
        secrets = _b64({"banco_de_chile": "pass1", "banco_consorcio": "pass2"})

        users = parse_multi_credentials(ids, secrets)

        assert len(users) == 2
        by_connector = {u.connector_id: u for u in users}
        assert by_connector["banco_de_chile"].clientId == "11111111-1"
        assert by_connector["banco_de_chile"].clientSecret == "pass1"
        assert by_connector["banco_consorcio"].clientId == "22222222-2"
        assert by_connector["banco_consorcio"].clientSecret == "pass2"

    def test_single_institution_base64(self):
        ids = _b64({"banco_de_chile": "11111111-1"})
        secrets = _b64({"banco_de_chile": "pass1"})

        users = parse_multi_credentials(ids, secrets)

        assert len(users) == 1
        assert users[0].connector_id == "banco_de_chile"
        assert users[0].clientId == "11111111-1"

    def test_missing_password_raises(self):
        ids = _b64({"banco_de_chile": "11111111-1", "banco_consorcio": "22222222-2"})
        secrets = _b64({"banco_de_chile": "pass1"})  # missing banco_consorcio

        with pytest.raises(CredentialError, match="Missing password"):
            parse_multi_credentials(ids, secrets)

    def test_empty_dict_raises(self):
        ids = _b64({})
        secrets = _b64({})

        with pytest.raises(CredentialError, match="No institutions found"):
            parse_multi_credentials(ids, secrets)


class TestLegacyFormat:
    def test_plain_rut(self):
        users = parse_multi_credentials("12345678-9", "mypassword")

        assert len(users) == 1
        assert users[0].clientId == "12345678-9"
        assert users[0].clientSecret == "mypassword"
        assert users[0].connector_id == "banco_de_chile"

    def test_connector_prefix(self):
        users = parse_multi_credentials("banco_consorcio;12345678-9", "mypassword")

        assert len(users) == 1
        assert users[0].connector_id == "banco_consorcio"
        assert users[0].clientId == "12345678-9"
