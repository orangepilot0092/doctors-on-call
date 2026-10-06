from app.core.llm_providers import LLMProviderFactory, LLMProvider

class LLMClient:
    """
    High-level LLM client used by the business logic (e.g., AI Matching, WhatsApp Bot).
    Delegates all actual API calls to the configured provider (Groq, Ollama).
    """
    def __init__(self):
        self.provider: LLMProvider = LLMProviderFactory.get_provider()

    async def extract_json(self, prompt: str, system_prompt: str = "") -> dict:
        return await self.provider.generate_json(prompt, system_prompt)

llm_client = LLMClient()
