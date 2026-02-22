import base64
import json
import logging

from ahorratron.sync_api.models.core_models import UserData

logger = logging.getLogger(__name__)


class CredentialError(ValueError):
    """Raised when multi-bank credentials are structurally valid base64 JSON
    but have a logical error (e.g. missing password for an institution)."""


def parse_multi_credentials(client_id: str, client_secret: str) -> list[UserData]:
    """Parse credentials into a list of UserData for one or more institutions.

    Supports two formats:

    1. **Multi-bank (base64 JSON)**::

        clientId:     base64({"banco_de_chile": "12345678-9", "banco_consorcio": "98765432-1"})
        clientSecret: base64({"banco_de_chile": "pass1", "banco_consorcio": "pass2"})

    2. **Single-bank (legacy)**::

        clientId:     "banco_de_chile;12345678-9"   (or just "12345678-9")
        clientSecret: "password"
    """
    try:
        ids = json.loads(base64.b64decode(client_id))
        secrets = json.loads(base64.b64decode(client_secret))
        if isinstance(ids, dict) and isinstance(secrets, dict):
            users: list[UserData] = []
            for connector_id, rut in ids.items():
                if connector_id not in secrets:
                    raise CredentialError(
                        f"Missing password for institution '{connector_id}'"
                    )
                users.append(
                    UserData(
                        clientId=rut,
                        clientSecret=secrets[connector_id],
                        connector_id=connector_id,
                    )
                )
            if not users:
                raise CredentialError("No institutions found in credentials")
            logger.info(
                "Parsed multi-bank credentials for: %s",
                [u.connector_id for u in users],
            )
            return users
    except CredentialError:
        raise
    except Exception as exc:
        logger.debug("Not multi-bank format (%s), falling back to single-bank", exc)

    # Fallback: single institution (old format — connector_id;rut or just rut)
    return [UserData(clientId=client_id, clientSecret=client_secret)]
