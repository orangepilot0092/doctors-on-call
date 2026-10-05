from pydantic import BaseModel, Field

# Mobile OTP Schemas
class GenerateMobileOTPRequest(BaseModel):
    hpr_token: str = Field(..., description="HPR Token obtained from login")
    officialMobile: str = Field(..., description="Mobile number (plain or encrypted as per ABDM sandbox requirements)")

class VerifyMobileOTPRequest(BaseModel):
    hpr_token: str = Field(...)
    txnId: str = Field(..., description="Transaction ID received from generate/regenerate OTP response")
    otp: str = Field(..., description="6-digit OTP (plain or encrypted)")

# Email OTP Schemas
class GenerateEmailOTPRequest(BaseModel):
    hpr_token: str = Field(...)
    emailAddress: str = Field(...)
    otp_type: str = Field(default="official", description="Typically 'official'")

class VerifyEmailOTPRequest(BaseModel):
    hpr_token: str = Field(...)
    hpr_id: str = Field(..., description="Healthcare Professional ID")
    officialEmail: str = Field(...)
    emailOtp: str = Field(..., description="6-digit Email OTP")
