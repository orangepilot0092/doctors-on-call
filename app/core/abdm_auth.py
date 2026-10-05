import httpx
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from app.core.config import settings
from app.core.abdm_client import abdm_client

class ABDMAuthClient:
    def __init__(self):
        self.hpr_base_url = settings.ABDM_HPR_URL

    async def _get_auth_headers(self) -> dict:
        """Fetches the Gateway Token and formats the Authorization header."""
        token = await abdm_client.get_gateway_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    def _encrypt_otp(self, otp: str, public_key_pem: str) -> str:
        """
        Encrypts the OTP using RSA with PKCS1v1.5 padding.
        This matches the ABDM requirement: RSA/ECB/PKCS1Padding.
        """
        # Clean and format the PEM string
        pem_bytes = public_key_pem.strip().encode('utf-8')
        if not pem_bytes.startswith(b'-----BEGIN PUBLIC KEY-----'):
            pem_bytes = b"-----BEGIN PUBLIC KEY-----\n" + pem_bytes + b"\n-----END PUBLIC KEY-----"
        
        public_key = serialization.load_pem_public_key(pem_bytes)
        
        # Encrypt using PKCS1v15 (Equivalent to RSA/ECB/PKCS1Padding)
        encrypted_bytes = public_key.encrypt(
            otp.encode('utf-8'),
            padding.PKCS1v15()
        )
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    async def login_via_password(self, hpr_id: str, password: str) -> dict:
        """Login via HPR ID and Password."""
        headers = await self._get_auth_headers()
        payload = {
            "idType": "hpr_id",
            "domainName": "@hpr.abdm",
            "hprId": hpr_id,
            "password": password
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{self.hpr_base_url}/v1/auth/authPassword",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def login_via_mobile_otp(self, mobile: str, otp: str) -> dict:
        """
        Login via Mobile OTP. 
        This is a 4-step process: Send OTP -> Get Cert -> Verify OTP (Encrypted) -> Final Login.
        """
        headers = await self._get_auth_headers()
        
        # Step 1: Send OTP
        async with httpx.AsyncClient(timeout=10.0) as client:
            send_resp = await client.post(
                f"{self.hpr_base_url}/v2/auth/loginViaMobileSendOTP",
                headers=headers,
                json={"mobile": mobile}
            )
            send_resp.raise_for_status()
            txn_id = send_resp.json()["txnId"]

        # Step 2: Get Public Certificate
        async with httpx.AsyncClient(timeout=10.0) as client:
            cert_resp = await client.get(
                f"{self.hpr_base_url}/v1/auth/cert",
                headers=headers
            )
            cert_resp.raise_for_status()
            public_key_pem = cert_resp.text

        # Step 3: Encrypt OTP and Verify
        encrypted_otp = self._encrypt_otp(otp, public_key_pem)
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_resp = await client.post(
                f"{self.hpr_base_url}/v2/auth/loginViaMobileSendOTP",
                headers=headers,
                json={"otp": encrypted_otp, "txnId": txn_id}
            )
            verify_resp.raise_for_status()
            # Extract the masked HPR ID Number to complete the login
            hpr_id_number = verify_resp.json()["mobileLinkedHpIdDTO"][0]["hprIdNumber"]

        # Step 4: Final Login with HPRID
        async with httpx.AsyncClient(timeout=10.0) as client:
            login_resp = await client.post(
                f"{self.hpr_base_url}/v2/auth/login/userAuthorizedToken",
                headers=headers,
                json={"hpId": hpr_id_number, "txnId": txn_id}
            )
            login_resp.raise_for_status()
            return login_resp.json()

    async def login_via_aadhaar_otp(self, hpr_id: str, otp: str) -> dict:
        """Login via Aadhaar OTP."""
        headers = await self._get_auth_headers()
        
        # Step 1: Init Aadhaar OTP
        async with httpx.AsyncClient(timeout=10.0) as client:
            init_resp = await client.post(
                f"{self.hpr_base_url}/v1/auth/init",
                headers=headers,
                json={
                    "idType": "hpr_id",
                    "domainName": "@hpr.abdm",
                    "authMethod": "AADHAAR OTP",
                    "hprId": hpr_id
                }
            )
            init_resp.raise_for_status()
            txn_id = init_resp.json()["txnId"]

        # Step 2: Verify Aadhaar OTP
        async with httpx.AsyncClient(timeout=10.0) as client:
            verify_resp = await client.post(
                f"{self.hpr_base_url}/v1/auth/confirmWithAadhaarOtp",
                headers=headers,
                json={"otp": otp, "txnId": txn_id}
            )
            verify_resp.raise_for_status()
            return verify_resp.json()

# Instantiate a singleton client for the application
abdm_auth_client = ABDMAuthClient()
