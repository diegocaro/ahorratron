"""Authentication utilities for the API"""

from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from ahorratron.api.config import get_settings

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from the X-API-KEY header.

    Args:
        api_key: The API key from the header

    Returns:
        The verified API key

    Raises:
        HTTPException: If the API key is invalid
    """
    settings = get_settings()
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"},
        )

    return api_key
