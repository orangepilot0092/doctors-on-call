from app.core.whatsapp_providers import WhatsAppProviderFactory, WhatsAppProvider

class WhatsAppClient:
    """
    High-level WhatsApp client used by the business logic.
    Delegates all actual API calls to the configured provider (Meta, Gupshup, etc.).
    """
    def __init__(self):
        self.provider: WhatsAppProvider = WhatsAppProviderFactory.get_provider()

    async def send_text_message(self, to: str, body: str) -> dict:
        return await self.provider.send_text_message(to, body)

    async def send_template_message(self, to: str, template_name: str, parameters: list) -> dict:
        return await self.provider.send_template_message(to, template_name, parameters)

wa_client = WhatsAppClient()
