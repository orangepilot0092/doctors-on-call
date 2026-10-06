from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.models.shift import Shift, ShiftStatus
from app.models.facility import Facility
from app.services.geofence_service import calculate_distance_meters

router = APIRouter(prefix="/attendance", tags=["Shift Attendance & Geofencing"])

class LocationPayload(BaseModel):
    doctor_id: int
    latitude: float
    longitude: float

@router.post("/shifts/{shift_id}/check-in")
async def check_in(shift_id: int, data: LocationPayload, db: AsyncSession = Depends(get_db)):
    """
    Doctor checks in to a shift. Validates they are within 200 meters of the hospital.
    """
    # 1. Fetch Shift
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift: raise HTTPException(404, "Shift not found")
    if shift.status != ShiftStatus.ASSIGNED: raise HTTPException(400, f"Shift is not active (Status: {shift.status})")
    if shift.assigned_doctor_id != data.doctor_id: raise HTTPException(403, "You are not assigned to this shift")
    if shift.check_in_time: raise HTTPException(400, "You have already checked in for this shift")
    
    # 2. Fetch Hospital Facility Coordinates
    fac_stmt = select(Facility).where(Facility.id == shift.facility_id)
    fac_result = await db.execute(fac_stmt)
    facility = fac_result.scalar_one()
    
    if not facility.latitude or not facility.longitude:
        raise HTTPException(500, "Hospital GPS coordinates missing in database")
        
    # 3. Calculate Distance
    distance = calculate_distance_meters(data.latitude, data.longitude, facility.latitude, facility.longitude)
    
    # 4. Enforce 200-meter Geofence
    if distance > 200:
        raise HTTPException(
            400, 
            f"❌ Check-in REJECTED: You are {distance:.0f} meters away from {facility.name}. You must be within 200 meters to check in."
        )
        
    # 5. Record Check-in
    shift.check_in_time = datetime.utcnow()
    shift.check_in_lat = data.latitude
    shift.check_in_lon = data.longitude
    await db.commit()
    
    return {
        "message": f"✅ Check-in successful! You are {distance:.0f}m from {facility.name}.",
        "shift_id": shift_id,
        "check_in_time": shift.check_in_time.isoformat()
    }

@router.post("/shifts/{shift_id}/check-out")
async def check_out(shift_id: int, data: LocationPayload, db: AsyncSession = Depends(get_db)):
    """
    Doctor checks out of a shift. Validates they are still at the hospital.
    """
    stmt = select(Shift).where(Shift.id == shift_id)
    result = await db.execute(stmt)
    shift = result.scalar_one_or_none()
    
    if not shift: raise HTTPException(404, "Shift not found")
    if not shift.check_in_time: raise HTTPException(400, "Cannot check out before checking in")
    if shift.check_out_time: raise HTTPException(400, "You have already checked out")
    
    fac_stmt = select(Facility).where(Facility.id == shift.facility_id)
    fac_result = await db.execute(fac_stmt)
    facility = fac_result.scalar_one()
    
    distance = calculate_distance_meters(data.latitude, data.longitude, facility.latitude, facility.longitude)
    
    if distance > 200:
        raise HTTPException(
            400, 
            f"❌ Check-out REJECTED: You are {distance:.0f} meters away. Please return to the hospital ward to check out."
        )
        
    shift.check_out_time = datetime.utcnow()
    shift.check_out_lat = data.latitude
    shift.check_out_lon = data.longitude
    shift.status = ShiftStatus.COMPLETED
    await db.commit()
    
    return {
        "message": f"✅ Shift completed! Payment processing initiated.",
        "shift_id": shift_id,
        "check_out_time": shift.check_out_time.isoformat()
    }
