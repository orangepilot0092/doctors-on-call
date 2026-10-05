import httpx
from app.core.config import settings

class WhatsAppClient:
    def __init__(self):
        self.phone_number_id = getattr(settings, "WA_PHONE_NUMBER_ID", "test_id")
        self.access_token = getattr(settings, "WA_ACCESS_TOKEN", "test_token")
        self.api_version = getattr(settings, "WA_API_VERSION", "v19.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    async def send_text_message(self, to: str, body: str) -> dict:
        # Placeholder for now; full implementation in Sprint 8
        return {"status": "sent", "to": to, "body": body}

wa_client = WhatsAppClient()
