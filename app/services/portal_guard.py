from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.hospital_admin import HospitalAdmin
from app.models.facility import Facility

async def is_facility_verified(db: AsyncSession, admin_email: str) -> bool:
    """Checks if the hospital admin's linked facility is verified."""
    stmt = select(HospitalAdmin).where(HospitalAdmin.email == admin_email)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()
    
    if not admin: return False
    
    fac_stmt = select(Facility).where(Facility.id == admin.facility_id)
    fac_result = await db.execute(fac_stmt)
    facility = fac_result.scalar_one_or_none()
    
    return facility.is_verified if facility else False
