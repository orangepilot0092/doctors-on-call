from fastapi import APIRouter, HTTPException
from app.core.abdm_auth import abdm_auth_client

router = APIRouter(prefix="/auth", tags=["ABDM Authentication"])

@router.post("/login/password")
async def login_password(hpr_id: str, password: str):
    try:
        return await abdm_auth_client.login_via_password(hpr_id, password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/mobile-otp")
async def login_mobile_otp(mobile: str, otp: str):
    try:
        return await abdm_auth_client.login_via_mobile_otp(mobile, otp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login/aadhaar-otp")
async def login_aadhaar_otp(hpr_id: str, otp: str):
    try:
        return await abdm_auth_client.login_via_aadhaar_otp(hpr_id, otp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
