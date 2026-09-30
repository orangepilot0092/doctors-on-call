from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.db.database import get_db
from app.models.shift import ShiftRequest
from app.schemas.shift import ShiftCreateRequest, ShiftResponse, ShiftStatusResponse
from app.services.matching import simulate_ai_matching_and_notify_founder

router = APIRouter(prefix="/api/v1/pilot", tags=["Pilot MVP"])


@router.post("/request-shift", response_model=ShiftResponse)
async def create_shift_request(
    request: ShiftCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Clinic submits a shift request."""
    new_shift = ShiftRequest(
        clinic_name=request.clinic_name,
        clinic_pincode=request.clinic_pincode,
        specialty=request.specialty,
        shift_date=request.shift_date,
        shift_time=request.shift_time,
        reason_posted=request.reason_posted,
        current_sourcing_method=request.current_sourcing_method,
    )
    db.add(new_shift)
    await db.commit()
    await db.refresh(new_shift)

    background_tasks.add_task(
        simulate_ai_matching_and_notify_founder,
        str(new_shift.id),
        db,
    )

    return ShiftResponse(
        id=new_shift.id,
        status="matching",
        message="Requirement received. Analyzing verified doctors in your area...",
    )


@router.get("/shifts", response_model=List[ShiftStatusResponse])
async def list_shifts(db: AsyncSession = Depends(get_db)):
    """List all shift requests."""
    result = await db.execute(
        select(ShiftRequest).order_by(ShiftRequest.created_at.desc())
    )
    return result.scalars().all()


@router.get("/shifts/{shift_id}", response_model=ShiftStatusResponse)
async def get_shift(shift_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get details of a specific shift."""
    result = await db.execute(select(ShiftRequest).where(ShiftRequest.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift
