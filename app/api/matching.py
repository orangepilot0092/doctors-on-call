from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.matching_service import find_matching_doctors

router = APIRouter(prefix="/matching", tags=["Shift Matching Engine"])

@router.post("/find-doctors/{shift_id}")
async def get_matching_doctors(shift_id: int, db: AsyncSession = Depends(get_db)):
    """
    Finds and ranks the best doctors for a specific shift based on 
    specialty and transit corridor compatibility.
    """
    try:
        matches = await find_matching_doctors(db, shift_id)
        return {
            "shift_id": shift_id,
            "total_matches": len(matches),
            "ranked_doctors": matches
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
