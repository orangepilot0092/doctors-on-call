import httpx
from fastapi import APIRouter, HTTPException
from app.core.abdm_client import abdm_client

router = APIRouter(prefix="/abdm", tags=["ABDM Integration"])

@router.get("/gateway-token")
async def test_gateway_token():
    """
    Test endpoint to fetch and return the ABDM Gateway Token.
    """
    try:
        token = await abdm_client.get_gateway_token()
        return {
            "status": "success",
            "message": "Gateway token fetched successfully",
            "token_preview": f"{token[:50]}..."  # Return a preview for security
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code, 
            detail=f"ABDM API Error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Gateway Token: {str(e)}")
