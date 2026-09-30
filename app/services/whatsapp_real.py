"""
Real WhatsApp Business API via Wati.io
Pricing: ₹3,500/mo for 1000 conversations
Get API key: https://wati.io

Alternative: Gupshup (https://gupshup.io) - even cheaper
"""
import httpx
import asyncio
from typing import List, Dict, Optional
from app.core.config import get_settings

settings = get_settings()

# Wati API credentials (get from wati.io dashboard)
WATI_API_KEY = "YOUR_WATI_API_KEY"
WATI_ENDPOINT = "https://live-server.wati.io/DocOnCall"  # Your subdomain

# Fallback: Use Gupshup (cheaper, ₹0.03 per message)
GUPSHUP_API_KEY = "YOUR_GUPSHUP_KEY"
GUPSHUP_APP_ID = "YOUR_APP_ID"


class WhatsAppService:
    """Real WhatsApp messaging via Wati Business API"""
    
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {WATI_API_KEY}",
            "Content-Type": "application/json"
        }
    
    async def send_text_message(self, phone: str, message: str) -> bool:
        """Send plain text WhatsApp message"""
        try:
            # Wati API format
            url = f"{WATI_ENDPOINT}/api/v1/sendMessage"
            
            payload = {
                "whatsappNumber": phone,
                "message": message,
                "type": "text"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"✅ WhatsApp sent to {phone}")
                    return True
                else:
                    print(f"❌ WhatsApp failed: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ WhatsApp error: {e}")
            return False
    
    async def send_shift_offer(
        self,
        doctor_phone: str,
        doctor_name: str,
        clinic_name: str,
        location: str,
        specialty: str,
        shift_date: str,
        shift_time: str,
        payout: float,
        shift_id: str
    ) -> bool:
        """Send interactive shift offer with YES/NO buttons"""
        
        message = f"""🩺 *New Shift Opportunity*

Hi Dr. {doctor_name},

We have a shift matching your profile:

📍 *Clinic:* {clinic_name}
📍 *Location:* {location}
📋 *Specialty:* {specialty}
📅 *Date:* {shift_date}
⏰ *Time:* {shift_time}
💰 *Payout:* ₹{payout:,.0f}

Reply YES to accept or NO to decline.
You have 30 minutes to respond.

- DOCTORS ON CALL"""
        
        return await self.send_text_message(doctor_phone, message)
    
    async def send_shift_confirmation(
        self,
        clinic_phone: str,
        clinic_name: str,
        doctor_name: str,
        shift_date: str,
        shift_time: str
    ) -> bool:
        """Confirm doctor acceptance to clinic"""
        
        message = f"""✅ *Shift Confirmed*

Hi {clinic_name},

Your shift has been filled!

👨‍⚕️ *Doctor:* Dr. {doctor_name}
📅 *Date:* {shift_date}
⏰ *Time:* {shift_time}

The doctor will arrive 15 minutes early.
Please confirm attendance at end of shift.

- DOCTORS ON CALL"""
        
        return await self.send_text_message(clinic_phone, message)
    
    async def send_payment_receipt(
        self,
        customer_phone: str,
        customer_name: str,
        plan_name: str,
        amount: float,
        payment_id: str
    ) -> bool:
        """Send subscription payment receipt"""
        
        message = f"""💳 *Payment Successful*

Hi {customer_name},

Your subscription payment was successful.

📋 *Plan:* {plan_name}
💰 *Amount:* ₹{amount:,.2f}
🆔 *Payment ID:* {payment_id[:12]}

Thank you for choosing DOCTORS ON CALL!

Need help? Reply to this message.

- Team DOCTORS ON CALL"""
        
        return await self.send_text_message(customer_phone, message)
    
    async def send_broadcast(self, phone_numbers: List[str], message: str) -> Dict:
        """Send broadcast message to multiple doctors"""
        success_count = 0
        fail_count = 0
        
        for phone in phone_numbers:
            result = await self.send_text_message(phone, message)
            if result:
                success_count += 1
            else:
                fail_count += 1
            
            # Rate limiting: 1 message per second
            await asyncio.sleep(1)
        
        return {
            "total": len(phone_numbers),
            "sent": success_count,
            "failed": fail_count
        }


# Singleton
whatsapp_service = WhatsAppService()
