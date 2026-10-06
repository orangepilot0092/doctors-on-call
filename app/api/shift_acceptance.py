from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.shift import Shift, ShiftStatus
from app.services.shift_lock_service import ShiftLockService

router = APIRouter(prefix="/shifts", tags=["Shift Acceptance"])

@router.post("/{shift_id}/accept")
async def accept_shift(shift_id: int, doctor_id: int, db: AsyncSession = Depends(get_db)):
    """
    Allows a doctor to accept a shift.
    Uses Redis distributed locks to prevent double-booking race conditions.
    """
    # 1. Attempt to acquire the distributed lock
    lock_acquired = await ShiftLockService.acquire_lock(shift_id, doctor_id)
    
    if not lock_acquired:
        # Another doctor is currently processing this exact shift
        current_owner = await ShiftLockService.get_lock_owner(shift_id)
        raise HTTPException(
            status_code=409, 
            detail=f"Conflict: Shift is currently being processed by Doctor {current_owner}. Please try another shift."
        )
        
    try:
        # 2. Fetch the shift from DB
        stmt = select(Shift).where(Shift.id == shift_id)
        result = await db.execute(stmt)
        shift = result.scalar_one_or_none()
        
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
            
        # 3. Check if shift is still OPEN
        if shift.status != ShiftStatus.OPEN:
            raise HTTPException(
                status_code=400, 
                detail=f"Shift is no longer available. Current status: {shift.status}"
            )
            
        # 4. Assign the doctor and update status
        shift.assigned_doctor_id = doctor_id
        shift.status = ShiftStatus.ASSIGNED
        
        await db.commit()
        
        return {
            "message": "Shift accepted successfully!",
            "shift_id": shift_id,
            "doctor_id": doctor_id,
            "new_status": shift.status
        }
        
    finally:
        # 5. ALWAYS release the lock, even if an error occurred
        await ShiftLockService.release_lock(shift_id)
