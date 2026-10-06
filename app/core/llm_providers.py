"""
LLM Provider Abstraction Layer.
Allows seamless swapping between Cloud (Groq) and Local (Ollama) models.
"""
import os
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from groq import Groq, AsyncGroq
from app.core.config import settings

class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str, system_prompt: str = "") -> dict:
        pass

class GroqProvider(LLMProvider):
    """Groq API: Blazing fast cloud inference (Llama 3 70B)"""
    def __init__(self):
        self.api_key = getattr(settings, "GROQ_API_KEY", "test_key")
        self.model = getattr(settings, "GROQ_MODEL", "llama3-70b-8192")
        self.client = AsyncGroq(api_key=self.api_key)

    async def generate_json(self, prompt: str, system_prompt: str = "You are a helpful assistant that outputs strict JSON.") -> dict:
        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1
            )
            import json
            return json.loads(chat_completion.choices[0].message.content)
        except Exception as e:
            return {"status": "error", "provider": "groq", "error": str(e)}

class OllamaProvider(LLMProvider):
    """Ollama: Private, free local inference"""
    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = getattr(settings, "OLLAMA_MODEL", "llama3")

    async def generate_json(self, prompt: str, system_prompt: str = "You are a helpful assistant that outputs strict JSON.") -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "format": "json",
            "stream": False
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                import json
                return json.loads(response.json()["message"]["content"])
            except Exception as e:
                return {"status": "error", "provider": "ollama", "error": str(e)}

class LLMProviderFactory:
    @staticmethod
    def get_provider() -> LLMProvider:
        # Bulletproof OS env check
        provider_name = os.environ.get("LLM_PROVIDER", getattr(settings, "LLM_PROVIDER", "groq")).lower()
        
        if provider_name == "ollama":
            return OllamaProvider()
        elif provider_name == "groq":
            return GroqProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
