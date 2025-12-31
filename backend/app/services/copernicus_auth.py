"""
Copernicus Data Space API OAuth2 authentication
"""

import httpx
from app.config import settings
from typing import Optional, Dict
import time

# Token cache
_token_cache: Optional[Dict[str, any]] = None


async def get_access_token() -> Optional[str]:
    """
    Get OAuth2 access token from Copernicus Data Space API
    
    Returns:
        Access token string or None if authentication fails
    """
    global _token_cache
    
    # Check if we have a valid cached token
    if _token_cache and _token_cache.get('expires_at', 0) > time.time():
        return _token_cache.get('access_token')
    
    if not settings.copernicus_client_id or not settings.copernicus_client_secret:
        print("[Copernicus Auth] Missing credentials")
        return None
    
    # OAuth2 token endpoint
    token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.copernicus_client_id,
                    "client_secret": settings.copernicus_client_secret,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                access_token = data.get("access_token")
                expires_in = data.get("expires_in", 3600)  # Default 1 hour
                
                # Cache the token
                _token_cache = {
                    "access_token": access_token,
                    "expires_at": time.time() + expires_in - 60  # Refresh 1 minute early
                }
                
                print("[Copernicus Auth] Successfully authenticated")
                return access_token
            else:
                print(f"[Copernicus Auth] Authentication failed: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"[Copernicus Auth] Error during authentication: {e}")
        return None


async def get_authenticated_client() -> Optional[httpx.AsyncClient]:
    """
    Get an authenticated httpx client with access token
    
    Returns:
        httpx.AsyncClient with authorization header or None
    """
    token = await get_access_token()
    if not token:
        return None
    
    return httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=30.0
    )

