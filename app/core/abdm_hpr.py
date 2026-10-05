import httpx
import base64
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.abdm_client import abdm_client

class ABDMHPRClient:
    def __init__(self):
        self.base_url = settings.ABDM_HPR_URL.rstrip('/')

    async def _get_headers(self, hpr_token: str) -> tuple:
        gateway_token = await abdm_client.get_gateway_token()
        return {
            "Authorization": f"Bearer {gateway_token}",
            "Content-Type": "application/json"
        }, hpr_token

    async def fetch_professional_info(self, hpr_id: str) -> dict:
        headers, _ = await self._get_headers("")
        payload = {"practitioner": {"id": hpr_id}}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/fetch-professional-info",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def update_professional(self, payload: dict) -> dict:
        hpr_token = payload.pop("hpr_token")
        headers, _ = await self._get_headers(hpr_token)
        payload["hpr_token"] = hpr_token
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/update-professional-new",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def fetch_documents_list(self, hpr_id: str) -> dict:
        headers, _ = await self._get_headers("")
        payload = {"hprid": hpr_id}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/fetch-documents-list",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def upload_document(self, hpr_token: str, documents: list) -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {"hpr_token": hpr_token, "document": documents}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/uploads/upload-document",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    # ==========================================
    # MOBILE OTP VERIFICATION FLOWS
    # ==========================================
    async def generate_mobile_otp(self, hpr_token: str, official_mobile: str) -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {"hpr_token": hpr_token, "officialMobile": official_mobile}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/generate-mobile-otp",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def regenerate_mobile_otp(self, hpr_token: str, official_mobile: str) -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {"hpr_token": hpr_token, "officialMobile": official_mobile}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/regenerate-mobile-otp",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def verify_mobile_otp(self, hpr_token: str, txn_id: str, otp: str) -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {"hpr_token": hpr_token, "txnId": txn_id, "otp": otp}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/verify-mobile-otp",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    # ==========================================
    # EMAIL OTP VERIFICATION FLOWS
    # ==========================================
    async def generate_email_otp(self, hpr_token: str, email_address: str, otp_type: str = "official") -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {"hpr_token": hpr_token, "emailAddress": email_address, "otp_type": otp_type}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/generate-verification-email",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def regenerate_email_otp(self, hpr_token: str, email_address: str, otp_type: str = "official") -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {"hpr_token": hpr_token, "emailAddress": email_address, "otp_type": otp_type}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/resent-verify-email",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def verify_email_otp(self, hpr_token: str, hpr_id: str, official_email: str, email_otp: str) -> dict:
        headers, _ = await self._get_headers(hpr_token)
        payload = {
            "hpr_token": hpr_token, 
            "hpr_id": hpr_id, 
            "officialEmail": official_email, 
            "emailOtp": email_otp
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/doctors/verify-email-otp",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

# Instantiate singleton
abdm_hpr_client = ABDMHPRClient()

# Helper function to validate and encode files
def validate_and_encode_file(file: UploadFile, doc_type: str) -> str:
    ALLOWED_TYPES = {
        "profilePhoto": {"image/png", "image/jpeg", "image/jpg"},
        "default": {"image/png", "image/jpeg", "image/jpg", "application/pdf"}
    }
    MAX_SIZE_PROFILE = 1 * 1024 * 1024  # 1 MB
    MAX_SIZE_OTHER = 5 * 1024 * 1024    # 5 MB
    
    max_size = MAX_SIZE_PROFILE if doc_type == "profilePhoto" else MAX_SIZE_OTHER
    allowed_types = ALLOWED_TYPES.get(doc_type, ALLOWED_TYPES["default"])
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_types}")
    
    file_content = file.file.read()
    if len(file_content) > max_size:
        limit_mb = 1 if doc_type == "profilePhoto" else 5
        raise HTTPException(status_code=400, detail=f"File size exceeds {limit_mb}MB limit.")
    
    return base64.b64encode(file_content).decode('utf-8')
