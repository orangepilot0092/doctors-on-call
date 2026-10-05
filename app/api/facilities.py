from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from app.models.facility import Facility
from app.db.session import get_db

router = APIRouter(prefix="/facilities", tags=["Facilities"])

class FacilityCreate(BaseModel):
    name: str
    location_area: str = "MMR"
    transit_corridor: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FacilityRead(BaseModel):
    id: int
    name: str
    location_area: str
    transit_corridor: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True

@router.post("/", status_code=201)
async def create_facility(facility: FacilityCreate, db: AsyncSession = Depends(get_db)):
    db_facility = Facility(**facility.model_dump())
    db.add(db_facility)
    await db.commit()
    await db.refresh(db_facility)
    return {"id": db_facility.id, "name": db_facility.name, "location": db_facility.location_area}

@router.get("/search", response_model=List[FacilityRead])
async def search_facilities(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = q.lower()
    result = await db.execute(
        select(Facility).where(
            or_(
                Facility.name.ilike(f"%{query}%"),
                Facility.location_area.ilike(f"%{query}%")
            )
        ).limit(limit)
    )
    return result.scalars().all()

@router.get("/count")
async def count_facilities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Facility))
    count = len(result.all())
    return {"total_facilities": count}
