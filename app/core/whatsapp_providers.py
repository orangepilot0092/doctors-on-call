"""
WhatsApp Provider Abstraction Layer.
"""
import os
from abc import ABC, abstractmethod
from typing import List
import httpx
from app.core.config import settings

class WhatsAppProvider(ABC):
    @abstractmethod
    async def send_text_message(self, to: str, body: str) -> dict:
        pass

    @abstractmethod
    async def send_template_message(self, to: str, template_name: str, parameters: List[str]) -> dict:
        pass

class MetaCloudProvider(WhatsAppProvider):
    def __init__(self):
        self.phone_number_id = getattr(settings, "WA_PHONE_NUMBER_ID", "test_id")
        self.access_token = getattr(settings, "WA_ACCESS_TOKEN", "test_token")
        self.api_version = getattr(settings, "WA_API_VERSION", "v19.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    async def send_text_message(self, to: str, body: str) -> dict:
        payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body}}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.base_url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"status": "error", "provider": "meta", "error": str(e)}

    async def send_template_message(self, to: str, template_name: str, parameters: List[str]) -> dict:
        return {"status": "error", "provider": "meta", "error": "Template not implemented in stub"}

class GupshupProvider(WhatsAppProvider):
    def __init__(self):
        self.api_key = getattr(settings, "GUPSHUP_API_KEY", "test_key")
        self.source = getattr(settings, "GUPSHUP_SOURCE", "DOCONC")
        self.base_url = "https://api.gupshup.io/sm/api/v1/msg"
        self.headers = {"apikey": self.api_key, "Content-Type": "application/x-www-form-urlencoded"}

    async def send_text_message(self, to: str, body: str) -> dict:
        payload = {
            "channel": "whatsapp", "source": self.source, "destination": to,
            "src.name": "DoctorsOnCall",
            "message": f'{{"isHSM":"false","type":"text","text":"{body}"}}'
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(self.base_url, headers=self.headers, data=payload)
                response.raise_for_status()
                return {"status": "sent", "provider": "gupshup", "response": response.json()}
            except Exception as e:
                return {"status": "error", "provider": "gupshup", "error": str(e)}

    async def send_template_message(self, to: str, template_name: str, parameters: List[str]) -> dict:
        return {"status": "error", "provider": "gupshup", "error": "Template not implemented in stub"}

class WhatsAppProviderFactory:
    @staticmethod
    def get_provider() -> WhatsAppProvider:
        # 🛡️ BULLETPROOF: Check OS environment directly first, then fallback to Pydantic settings
        provider_name = os.environ.get("WA_PROVIDER", getattr(settings, "WA_PROVIDER", "meta")).lower()
        
        if provider_name == "gupshup":
            return GupshupProvider()
        elif provider_name == "meta":
            return MetaCloudProvider()
        else:
            raise ValueError(f"Unsupported WhatsApp provider: {provider_name}")
