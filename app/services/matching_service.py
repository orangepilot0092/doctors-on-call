"""
Shift Matching Engine V1 (Rules-Based).

Calculates a Match Score for doctors based on:
1. Status (Must be VERIFIED or SHIFT_READY)
2. Specialty Match (+100 points)
3. Transit Corridor Match (+100 points) -> The Mumbai Moat
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.doctor_master_record import Doctor, DoctorStatus
from app.models.shift import Shift
from app.models.facility import Facility

async def find_matching_doctors(db: AsyncSession, shift_id: int) -> list[dict]:
    # 1. Fetch Shift and its Facility
    shift = (await db.execute(select(Shift).where(Shift.id == shift_id))).scalar_one_or_none()
    if not shift: raise ValueError("Shift not found")
    
    facility = (await db.execute(select(Facility).where(Facility.id == shift.facility_id))).scalar_one_or_none()
    shift_corridor = facility.transit_corridor if facility else "Unknown"
    shift_specialty = getattr(shift, 'required_specialty', None)

    # 2. Fetch all eligible doctors
    stmt = select(Doctor).where(Doctor.status.in_([DoctorStatus.VERIFIED, DoctorStatus.SHIFT_READY]))
    doctors = (await db.execute(stmt)).scalars().all()

    # 3. Score and Rank
    ranked_doctors = []
    for doc in doctors:
        score = 0
        reasons = []

        # Specialty Match
        if shift_specialty and doc.pg_specialty:
            if shift_specialty.lower() in doc.pg_specialty.lower():
                score += 100
                reasons.append(f"Specialty Match ({doc.pg_specialty})")
        
        # Transit Corridor Match (The Mumbai Moat!)
        if shift_corridor != "Unknown" and doc.home_transit_corridor:
            if shift_corridor.lower() == doc.home_transit_corridor.lower():
                score += 100
                reasons.append(f"Transit Match ({doc.home_transit_corridor} Line)")

        # Only return doctors with at least some relevance (or all if no specific requirements)
        if score > 0 or not (shift_specialty or shift_corridor):
            ranked_doctors.append({
                "doctor_id": doc.id,
                "doctor_code": doc.doctor_code,
                "name": doc.full_name,
                "match_score": score,
                "reasons": reasons,
                "home_corridor": doc.home_transit_corridor,
                "specialty": doc.pg_specialty
            })

    # Sort by score descending
    ranked_doctors.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked_doctors
