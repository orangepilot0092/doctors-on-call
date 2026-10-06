
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.services.payout_service import PayoutService
from app.models.shift import Shift

router = APIRouter(prefix="/payouts", tags=["Automated Payouts"])

class PayoutRequest(BaseModel):
    doctor_id: int

@router.post("/shifts/{shift_id}/trigger")
async def trigger_payout(shift_id: int, req: PayoutRequest, db: AsyncSession = Depends(get_db)):
    try:
        res = await PayoutService.process_instant_payout(db, shift_id, req.doctor_id)
        return {"message": "Instant payout triggered successfully via RazorpayX.", "details": res}
    except Exception as e:
        raise HTTPException(400, str(e))
