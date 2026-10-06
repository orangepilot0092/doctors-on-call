
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.shift import Shift
from app.services.negotiation_agent import negotiation_agent

router = APIRouter(prefix="/shifts", tags=["Shift Negotiation"])

class NegotiationRequest(BaseModel):
    doctor_message: str

@router.post("/{shift_id}/negotiate")
async def negotiate_shift(shift_id: int, req: NegotiationRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
        
    urgency_str = shift.urgency_level.value if hasattr(shift.urgency_level, 'value') else str(shift.urgency_level)
        
    evaluation = await negotiation_agent.evaluate_counter_offer(
        doctor_message=req.doctor_message,
        offered_rate=float(shift.offered_rate_inr),
        urgency_level=urgency_str
    )
    
    return {
        "shift_id": shift_id,
        "urgency": urgency_str,
        "base_rate": shift.offered_rate_inr,
        "ai_evaluation": evaluation
    }
