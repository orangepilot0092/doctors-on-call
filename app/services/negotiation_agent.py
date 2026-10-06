
import re
from app.core.llm_client import llm_client

URGENCY_BUFFERS = {
    "ROUTINE": 0.10,
    "URGENT": 0.25,
    "CRITICAL": 0.50
}

class NegotiationAgent:
    async def evaluate_counter_offer(self, doctor_message: str, offered_rate: float, urgency_level: str) -> dict:
        requested_rate = None
        
        try:
            system_prompt = "Extract the requested payment rate in INR. Return ONLY JSON: {'requested_rate': float}."
            llm_response = await llm_client.extract_json(doctor_message, system_prompt)
            if isinstance(llm_response, dict) and "requested_rate" in llm_response:
                requested_rate = float(llm_response["requested_rate"])
        except Exception:
            pass
            
        if requested_rate is None:
            match = re.search(r'\b(\d{3,6})\b', doctor_message)
            if match:
                requested_rate = float(match.group(1))
                
        if requested_rate is None:
            return {"decision": "CLARIFICATION_NEEDED", "message": "Please reply with your exact expected rate in INR."}
            
        buffer = URGENCY_BUFFERS.get(urgency_level.upper(), 0.10)
        max_allowed_rate = offered_rate * (1 + buffer)
        
        if requested_rate <= offered_rate:
            return {"decision": "ACCEPTED", "message": f"Great! We accept your rate of ₹{requested_rate}.", "final_rate": requested_rate}
        elif requested_rate <= max_allowed_rate:
            return {"decision": "ACCEPTED_WITH_BUFFER", "message": f"Given the {urgency_level} nature of this shift, we can accommodate ₹{requested_rate}.", "final_rate": requested_rate}
        else:
            return {"decision": "REJECTED", "message": f"Sorry, the maximum authorized budget for this {urgency_level} shift is ₹{max_allowed_rate:.0f}.", "final_rate": max_allowed_rate}

negotiation_agent = NegotiationAgent()
