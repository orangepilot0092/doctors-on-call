from fastapi import APIRouter, Request, HTTPException, Query
from app.core.config import settings

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
    return {"status": "ok"}
