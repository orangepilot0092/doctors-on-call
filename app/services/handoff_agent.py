
import json
from app.core.llm_client import llm_client

class HandoffAgent:
    async def generate_briefing(self, raw_notes: str) -> dict:
        # Regex fallback for when LLM is offline/rate-limited
        try:
            system_prompt = '''You are a medical handoff AI. Extract structured clinical data from raw notes. 
            Return ONLY JSON with keys: 
            'patients' (list of objects with 'bed', 'diagnosis', 'current_status', 'action_items', 'allergies').'''
            
            response = await llm_client.extract_json(raw_notes, system_prompt)
            if isinstance(response, dict) and "patients" in response:
                return response
        except Exception:
            pass
            
        # Fallback: Basic text structuring
        return {
            "status": "fallback_mode",
            "raw_notes": raw_notes,
            "message": "LLM offline. Please read raw notes carefully."
        }

handoff_agent = HandoffAgent()
