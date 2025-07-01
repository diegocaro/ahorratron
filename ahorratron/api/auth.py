"""
Authentication utilities for the API.
"""
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

# For demonstration purposes, using a simple API key
# In production, this should be loaded from environment variables or a secure configuration
API_KEY = "your-secret-api-key"

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify the API key from the X-API-KEY header.
    
    Args:
        api_key: The API key from the header
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: If the API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-KEY header is required",
            headers={"WWW-Authenticate": "API-Key"},
        )
    
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API-Key"},
        )
    
    return api_key