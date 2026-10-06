from fastapi import APIRouter, Request, HTTPException, Query
from app.core.config import settings
from app.core.whatsapp_client import wa_client
from app.core.bot_state import BotState
import httpx
import os

router = APIRouter(prefix="/wa", tags=["WhatsApp Integration"])

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    verify_token = getattr(settings, "WA_VERIFY_TOKEN", "doctors_on_call_webhook_verify")
    if hub_mode == "subscribe" and hub_token == verify_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("/webhook")
async def process_message(request: Request):
    body = await request.json()
    
    try:
        # Standard Meta Cloud API payload structure
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        
        if "messages" in value:
            message = value["messages"][0]
            from_number = message["from"]
            msg_type = message["type"]
            
            if msg_type == "text":
                text_body = message["text"]["body"].strip()
                await handle_text_message(from_number, text_body)
            elif msg_type == "image":
                # Doctor uploaded a photo (e.g., their MBBS certificate)
                media_id = message["image"]["id"]
                await handle_media_message(from_number, media_id)
                
    except Exception as e:
        print(f"Error processing webhook: {e}")
        
    return {"status": "ok"}

async def handle_text_message(phone: str, text: str):
    state_data = await BotState.get_state(phone)
    current_state = state_data["state"]
    context = state_data.get("context", {})
    
    if text.lower() in ["hi", "hello", "start", "join"]:
        await BotState.set_state(phone, BotState.STATES["WAITING_HPR_ID"])
        await wa_client.send_text_message(
            phone, 
            "👋 Welcome to *Doctors on Call* 🏥\n\nTo start your verification, please reply with your *10-digit Mobile Number*."
        )
        
    elif current_state == BotState.STATES["WAITING_HPR_ID"]:
        if text.isdigit() and len(text) == 10:
            await BotState.set_state(phone, "AWAITING_REG_CERT", {"mobile": text})
            await wa_client.send_text_message(
                phone, 
                f"🔒 Mobile {text} noted.\n\nNext, please upload a clear photo of your *Medical Registration Certificate*."
            )
        else:
            await wa_client.send_text_message(phone, "⚠️ Please enter a valid 10-digit mobile number.")
            
    elif current_state == "AWAITING_OCR_CONFIRMATION":
        if text.lower() in ["yes", "y", "correct"]:
            # In a real flow, we would now save this to the DB via onboarding_service
            await BotState.set_state(phone, BotState.STATES["ONBOARDED"])
            await wa_client.send_text_message(
                phone, 
                "✅ *Data Confirmed!*\n\nYour registration details have been saved. Our verification team will review your documents within 24 hours."
            )
        else:
            await BotState.set_state(phone, "AWAITING_REG_CERT")
            await wa_client.send_text_message(phone, "❌ Okay, please upload a clearer photo of your certificate again.")
            
    elif current_state == BotState.STATES["ONBOARDED"]:
        await wa_client.send_text_message(phone, "You are fully verified! Reply 'shifts' to see available locums near you.")
        
    else:
        await wa_client.send_text_message(phone, "Reply with *Hi* to start the onboarding process.")

async def handle_media_message(phone: str, media_id: str):
    state_data = await BotState.get_state(phone)
    current_state = state_data["state"]
    
    if current_state == "AWAITING_REG_CERT":
        await wa_client.send_text_message(phone, "⏳ Processing your certificate... Please wait.")
        
        # 🛡️ MVP MOCK: In production, we would use the provider API to download the media_id.
        # For the demo, we simulate the OCR result directly to prove the state machine flow.
        mock_ocr_text = "MAHARASHTRA MEDICAL COUNCIL\nReg No: MMC-998877\nName: Dr. Anita Desai"
        
        await BotState.set_state(phone, "AWAITING_OCR_CONFIRMATION", {"ocr_text": mock_ocr_text})
        
        await wa_client.send_text_message(
            phone, 
            f"📄 *Extracted Details:*\n\n{mock_ocr_text}\n\nIs this information correct? Reply *YES* to confirm or *NO* to re-upload."
        )
    else:
        await wa_client.send_text_message(phone, "Please reply with *Hi* to start onboarding before uploading documents.")
