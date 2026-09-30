"""
WhatsApp Notification Service for Pre-Seed Validation.

For pre-seed, we use a simple HTTP-based approach.
Options:
1. Twilio WhatsApp API (easiest, costs ~₹0.5 per message)
2. Wati.io (WhatsApp Business API, free tier available)
3. Manual fallback: Print to terminal + send SMS via Fast2SMS

This service is designed to be swappable.
"""
import asyncio
import httpx
from app.core.config import get_settings

settings = get_settings()


async def send_shift_offer_to_doctor(
    doctor_phone: str,
    doctor_name: str,
    clinic_name: str,
    location: str,
    specialty: str,
    shift_date: str,
    shift_time: str,
    payout: float
) -> bool:
    """
    Send WhatsApp shift offer to doctor.
    Returns True if sent successfully.
    """
    message = f"""🩺 *New Shift Opportunity - DOCTORS ON CALL*

Hi Dr. {doctor_name},

We have a shift matching your profile:

📍 *Clinic:* {clinic_name}
📍 *Location:* {location}
📋 *Specialty:* {specialty}
📅 *Date:* {shift_date}
⏰ *Time:* {shift_time}
💰 *Payout:* ₹{payout:,.0f}

*Reply YES to accept or NO to decline.*

You have 30 minutes to respond.
- Team Doctors On Call"""

    # For pre-seed validation, print to terminal first
    print(f"\n📱 WHATSAPP MESSAGE TO {doctor_phone}:")
    print(message)
    print("-" * 50)

    # TODO: Replace with actual WhatsApp API call
    # Example with Twilio:
    # twilio_account_sid = "your_sid"
    # twilio_auth_token = "your_token"
    # twilio_whatsapp_number = "whatsapp:+14155238886"
    # 
    # url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
    # data = {
    #     "From": twilio_whatsapp_number,
    #     "To": f"whatsapp:+91{doctor_phone}",
    #     "Body": message
    # }
    # auth = (twilio_account_sid, twilio_auth_token)
    # async with httpx.AsyncClient() as client:
    #     response = await client.post(url, data=data, auth=auth)
    #     return response.status_code == 201

    return True


async def send_shift_confirmation_to_clinic(
    clinic_name: str,
    doctor_name: str,
    shift_date: str,
    shift_time: str
) -> bool:
    """Send confirmation to clinic that doctor accepted."""
    message = f"""✅ *Shift Confirmed - DOCTORS ON CALL*

Hi {clinic_name},

Your shift has been filled!

👨‍⚕️ *Doctor:* Dr. {doctor_name}
📅 *Date:* {shift_date}
⏰ *Time:* {shift_time}

The doctor has been verified and will arrive 15 minutes early.
Please confirm attendance at the end of the shift.

- Team Doctors On Call"""

    print(f"\n📱 WHATSAPP CONFIRMATION TO CLINIC:")
    print(message)
    print("-" * 50)
    
    return True
