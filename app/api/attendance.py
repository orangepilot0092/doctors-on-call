from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.facility import Facility
from app.models.shift import Shift, ShiftStatus
from app.services.geofence_service import calculate_distance_meters
from app.services.ops_events import publish_ops_event

router = APIRouter(prefix="/attendance", tags=["Shift Attendance & Geofencing"])

GEOFENCE_RADIUS_METERS = 200


class LocationPayload(BaseModel):
    doctor_id: int
    latitude: float
    longitude: float


@router.post("/shifts/{shift_id}/check-in")
async def check_in(shift_id: int, data: LocationPayload, db: AsyncSession = Depends(get_db)):
    shift = (
        await db.execute(select(Shift).where(Shift.id == shift_id))
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    if shift.status != ShiftStatus.ASSIGNED:
        raise HTTPException(
            status_code=400,
            detail=f"Shift is not active (Status: {shift.status})",
        )

    if shift.assigned_doctor_id != data.doctor_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this shift")

    if shift.check_in_time is not None:
        raise HTTPException(status_code=400, detail="You have already checked in for this shift")

    facility = (
        await db.execute(select(Facility).where(Facility.id == shift.facility_id))
    ).scalar_one_or_none()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    if facility.latitude is None or facility.longitude is None:
        raise HTTPException(status_code=500, detail="Hospital GPS coordinates missing in database")

    distance = calculate_distance_meters(
        data.latitude,
        data.longitude,
        facility.latitude,
        facility.longitude,
    )

    if distance > GEOFENCE_RADIUS_METERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"❌ Check-in REJECTED: You are {distance:.0f} meters away from {facility.name}. "
                f"You must be within {GEOFENCE_RADIUS_METERS} meters to check in."
            ),
        )

    shift.check_in_time = datetime.now(timezone.utc)
    shift.check_in_lat = data.latitude
    shift.check_in_lon = data.longitude
    await db.commit()

    await publish_ops_event(shift.facility_id, "GPS_CHECK_IN", {
        "shift_id": shift.id,
        "doctor_id": data.doctor_id,
        "distance_meters": round(distance, 2),
        "latitude": data.latitude,
        "longitude": data.longitude,
    })

    return {
        "message": f"✅ Check-in successful! You are {distance:.0f}m from {facility.name}.",
        "shift_id": shift.id,
        "check_in_time": shift.check_in_time.isoformat(),
    }


@router.post("/shifts/{shift_id}/check-out")
async def check_out(shift_id: int, data: LocationPayload, db: AsyncSession = Depends(get_db)):
    shift = (
        await db.execute(select(Shift).where(Shift.id == shift_id))
    ).scalar_one_or_none()

    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    if shift.assigned_doctor_id != data.doctor_id:
        raise HTTPException(status_code=403, detail="You are not assigned to this shift")

    if shift.check_in_time is None:
        raise HTTPException(status_code=400, detail="Cannot check out before checking in")

    if shift.check_out_time is not None:
        raise HTTPException(status_code=400, detail="You have already checked out")

    facility = (
        await db.execute(select(Facility).where(Facility.id == shift.facility_id))
    ).scalar_one_or_none()

    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")

    if facility.latitude is None or facility.longitude is None:
        raise HTTPException(status_code=500, detail="Hospital GPS coordinates missing in database")

    distance = calculate_distance_meters(
        data.latitude,
        data.longitude,
        facility.latitude,
        facility.longitude,
    )

    if distance > GEOFENCE_RADIUS_METERS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"❌ Check-out REJECTED: You are {distance:.0f} meters away. "
                "Please return to the hospital ward to check out."
            ),
        )

    shift.check_out_time = datetime.now(timezone.utc)
    shift.check_out_lat = data.latitude
    shift.check_out_lon = data.longitude
    shift.status = ShiftStatus.COMPLETED
    await db.commit()

    await publish_ops_event(shift.facility_id, "GPS_CHECK_OUT", {
        "shift_id": shift.id,
        "doctor_id": data.doctor_id,
        "distance_meters": round(distance, 2),
        "latitude": data.latitude,
        "longitude": data.longitude,
    })

    return {
        "message": "✅ Shift completed! Payment processing initiated.",
        "shift_id": shift.id,
        "check_out_time": shift.check_out_time.isoformat(),
    }
