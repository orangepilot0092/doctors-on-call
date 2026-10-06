
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from app.db.session import get_db
from app.models.shift import Shift
from app.services.handoff_agent import handoff_agent

router = APIRouter(prefix="/shifts", tags=["Medical Handoff"])

class HandoffRequest(BaseModel):
    raw_clinical_notes: str

@router.post("/{shift_id}/handoff")
async def generate_handoff(shift_id: int, req: HandoffRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
        
    briefing = await handoff_agent.generate_briefing(req.raw_clinical_notes)
    
    return {
        "shift_id": shift_id,
        "facility_id": shift.facility_id,
        "medical_briefing": briefing
    }
