import httpx
import base64
import os
from fastapi import UploadFile, HTTPException
from app.core.config import settings
from app.core.abdm_client import abdm_client

class ABDMHPRClient:
    def __init__(self):
        # Use the sandbox URL from config, appending the specific API path
        self.base_url = settings.ABDM_HPR_URL.rstrip('/')

    async def _get_headers(self, hpr_token: str) -> dict:
        """Gets Gateway token for headers, and prepares hpr_token for body."""
        gateway_token = await abdm_client.get_gateway_token()
        return {
            "Authorization": f"Bearer {gateway_token}",
            "Content-Type": "application/json"
        }, hpr_token

    async def fetch_professional_info(self, hpr_id: str) -> dict:
        """Fetches professional details using HPR ID."""
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
        """Updates professional details. Payload must include hpr_token in the body."""
        hpr_token = payload.pop("hpr_token")
        headers, _ = await self._get_headers(hpr_token)
        
        # ABDM expects hpr_token inside the request body for this specific API
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
        """Fetches the list of documents and their internal ABDM identifiers."""
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
        """
        Uploads documents to ABDM. 
        documents: List of dicts with 'document_id', 'document_type', 'fileType', 'data' (base64)
        """
        headers, _ = await self._get_headers(hpr_token)
        payload = {
            "hpr_token": hpr_token,
            "document": documents
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/v4/int/apis/v1/uploads/upload-document",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

# Helper function to validate and encode files
def validate_and_encode_file(file: UploadFile, doc_type: str) -> str:
    """Validates file size and type, then returns Base64 string."""
    ALLOWED_TYPES = {
        "profilePhoto": {"image/png", "image/jpeg", "image/jpg"},
        "default": {"image/png", "image/jpeg", "image/jpg", "application/pdf"}
    }
    
    # Size limits in bytes
    MAX_SIZE_PROFILE = 1 * 1024 * 1024  # 1 MB
    MAX_SIZE_OTHER = 5 * 1024 * 1024    # 5 MB
    
    max_size = MAX_SIZE_PROFILE if doc_type == "profilePhoto" else MAX_SIZE_OTHER
    allowed_types = ALLOWED_TYPES.get(doc_type, ALLOWED_TYPES["default"])
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed_types}")
    
    # Read file and check size
    file_content = file.file.read()
    if len(file_content) > max_size:
        limit_mb = 1 if doc_type == "profilePhoto" else 5
        raise HTTPException(status_code=400, detail=f"File size exceeds {limit_mb}MB limit.")
    
    # Return raw Base64 string (no "data:application/pdf;base64," prefix as per ABDM docs)
    return base64.b64encode(file_content).decode('utf-8')

# Instantiate singleton
abdm_hpr_client = ABDMHPRClient()
