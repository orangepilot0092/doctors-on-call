from fastapi import APIRouter, HTTPException
from app.core.abdm_hpr import abdm_hpr_client
from app.schemas.verification import (
    GenerateMobileOTPRequest, VerifyMobileOTPRequest,
    GenerateEmailOTPRequest, VerifyEmailOTPRequest
)

router = APIRouter(prefix="/verification", tags=["ABDM Contact Verification"])

# --- Mobile OTP Endpoints ---
@router.post("/mobile/generate")
async def generate_mobile_otp(req: GenerateMobileOTPRequest):
    try:
        return await abdm_hpr_client.generate_mobile_otp(req.hpr_token, req.officialMobile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mobile/regenerate")
async def regenerate_mobile_otp(req: GenerateMobileOTPRequest):
    try:
        return await abdm_hpr_client.regenerate_mobile_otp(req.hpr_token, req.officialMobile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mobile/verify")
async def verify_mobile_otp(req: VerifyMobileOTPRequest):
    try:
        return await abdm_hpr_client.verify_mobile_otp(req.hpr_token, req.txnId, req.otp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Email OTP Endpoints ---
@router.post("/email/generate")
async def generate_email_otp(req: GenerateEmailOTPRequest):
    try:
        return await abdm_hpr_client.generate_email_otp(req.hpr_token, req.emailAddress, req.otp_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/email/regenerate")
async def regenerate_email_otp(req: GenerateEmailOTPRequest):
    try:
        return await abdm_hpr_client.regenerate_email_otp(req.hpr_token, req.emailAddress, req.otp_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/email/verify")
async def verify_email_otp(req: VerifyEmailOTPRequest):
    try:
        return await abdm_hpr_client.verify_email_otp(req.hpr_token, req.hpr_id, req.officialEmail, req.emailOtp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
