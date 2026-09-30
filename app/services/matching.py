import asyncio
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.shift import ShiftRequest, ShiftStatus
from app.core.config import get_settings

settings = get_settings()


async def simulate_ai_matching_and_notify_founder(shift_id: str, db: AsyncSession):
    """
    The 'Wizard of Oz' function.
    In reality, this pauses for 8 seconds to create the illusion of AI matching,
    then sends a Telegram alert to the founder to manually do the work.
    """
    # 1. Update status to MATCHING
    result = await db.execute(select(ShiftRequest).where(ShiftRequest.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        return

    shift.status = ShiftStatus.MATCHING
    await db.commit()

    # 2. The "AI is thinking" delay (8 seconds)
    await asyncio.sleep(8)

    # 3. Update status to NOTIFIED (founder has been alerted)
    shift.status = ShiftStatus.DOCTOR_NOTIFIED
    await db.commit()

    # 4. Send Telegram alert to founder
    await send_telegram_alert(shift)


async def send_telegram_alert(shift: ShiftRequest):
    """Send a Telegram message to the founder about the new shift."""
    if not settings.telegram_bot_token or settings.telegram_bot_token == "your_telegram_bot_token_here":
        print(f"🚨 FOUNDER ALERT (Telegram not configured): Manual matching required for Shift {shift.id}")
        print(f"   Clinic: {shift.clinic_name} ({shift.clinic_pincode})")
        print(f"   Specialty: {shift.specialty}")
        print(f"   Date/Time: {shift.shift_date} @ {shift.shift_time}")
        return

    message = (
        f"🚨 *NEW SHIFT REQUEST*\n\n"
        f"*Clinic:* {shift.clinic_name}\n"
        f"*Pincode:* {shift.clinic_pincode}\n"
        f"*Specialty:* {shift.specialty}\n"
        f"*Date:* {shift.shift_date}\n"
        f"*Time:* {shift.shift_time}\n\n"
        f"*Action Required:* Open Command Center to manually match."
    )

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                print(f"✅ Telegram alert sent for shift {shift.id}")
            else:
                print(f"❌ Telegram alert failed: {response.text}")
        except Exception as e:
            print(f"❌ Telegram alert error: {e}")
