from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.schemas.shift_extraction import ShiftExtractionRequest, ShiftExtractionResponse
from app.schemas.shift import ShiftCreate, ShiftRead
from app.core.extraction_engine import extraction_engine
from app.core.facility_matcher import facility_matcher
from app.services.shift_service import create_shift, get_shifts, get_shift_by_id
from app.db.session import get_db

router = APIRouter(prefix="/shifts", tags=["Shift Management"])

@router.post("/extract", response_model=ShiftExtractionResponse)
async def extract_shift(
    request: ShiftExtractionRequest,
    resolve_facility: bool = Query(True, description="Attempt to match hospital against database"),
    db: AsyncSession = Depends(get_db)
):
    """
    Parse a chaotic hospital message into a structured shift request.
    Optionally resolves the hospital name against the MMR facility database.
    """
    try:
        result = extraction_engine.extract(request.raw_text)
        
        # Attempt to resolve hospital against database
        if resolve_facility and result["hospital_metadata"]["name"]:
            match = await facility_matcher.match(
                db,
                result["hospital_metadata"]["name"],
                result["hospital_metadata"].get("location_area")
            )
            if match:
                result["hospital_metadata"]["name"] = match["name"]
                result["hospital_metadata"]["location_area"] = match["location_area"]
        
        return ShiftExtractionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.post("/", response_model=ShiftRead, status_code=201)
async def create_new_shift(shift_data: ShiftCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_shift(db, shift_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ShiftRead])
async def read_shifts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await get_shifts(db, skip=skip, limit=limit)

@router.get("/{shift_id}", response_model=ShiftRead)
async def read_shift(shift_id: int, db: AsyncSession = Depends(get_db)):
    db_shift = await get_shift_by_id(db, shift_id)
    if db_shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return db_shift
