import httpx
import uuid
from datetime import datetime, timezone
from app.core.config import settings
from app.core.redis import get_redis_client

class ABDMClient:
    def __init__(self):
        self.gateway_url = settings.ABDM_GATEWAY_URL
        self.client_id = settings.ABDM_CLIENT_ID
        self.client_secret = settings.ABDM_CLIENT_SECRET
        # 'sbx' for Sandbox, 'abdm' for Production
        self.x_cm_id = "sbx" 

    def _get_abdm_headers(self) -> dict:
        """Generates the mandatory ABDM headers for Gateway Token requests."""
        # ISO 8601 format with milliseconds and 'Z' suffix
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        return {
            "REQUEST-ID": str(uuid.uuid4()),
            "TIMESTAMP": timestamp,
            "X-CM-ID": self.x_cm_id,
            "Content-Type": "application/json"
        }

    async def get_gateway_token(self) -> str:
        """
        Fetches the ABDM Gateway Token. 
        Caches the token in Redis to avoid hitting the ABDM API on every request.
        """
        redis_client = await get_redis_client()
        
        # 1. Check Redis cache first
        cached_token = await redis_client.get("abdm:gateway_token")
        if cached_token:
            return cached_token.decode('utf-8')

        # 2. Fetch from ABDM API if not cached
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.gateway_url,
                headers=self._get_abdm_headers(),
                json={
                    "clientId": self.client_id,
                    "clientSecret": self.client_secret,
                    "grantType": "client_credentials"
                }
            )
            
            # Raise an exception for 4xx/5xx responses
            response.raise_for_status()
            data = response.json()
            
            token = data["accessToken"]
            expires_in = data["expiresIn"]  # Typically 1200 seconds (20 mins)
            
            # 3. Cache the token in Redis with a 60-second buffer before actual expiry
            # This prevents edge-case failures where a token expires mid-request
            cache_ttl = max(expires_in - 60, 60) 
            await redis_client.setex("abdm:gateway_token", cache_ttl, token)
            
            return token

# Instantiate a singleton client for the application
abdm_client = ABDMClient()
