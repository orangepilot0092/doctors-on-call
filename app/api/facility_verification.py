from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.facility import Facility

router = APIRouter(prefix="/facilities", tags=["Facility Verification"])

class FacilityClaimRequest(BaseModel):
    authorized_contact_name: str
    authorized_contact_phone: str
    gst_number: str

@router.post("/{facility_id}/claim")
async def claim_facility(
    facility_id: int, 
    claim_data: FacilityClaimRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Hospital Admin claims a facility from the 35k DB and submits verification details.
    Status remains is_verified=False until an operator approves it.
    """
    stmt = select(Facility).where(Facility.id == facility_id)
    result = await db.execute(stmt)
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
        
    facility.authorized_contact_name = claim_data.authorized_contact_name
    facility.authorized_contact_phone = claim_data.authorized_contact_phone
    facility.gst_number = claim_data.gst_number
    facility.is_verified = False # Pending operator review
    
    await db.commit()
    await db.refresh(facility)
    
    return {
        "message": "Facility claimed successfully. Pending operator verification.",
        "facility_id": facility.id,
        "facility_name": facility.name,
        "status": "pending_verification"
    }

@router.post("/{facility_id}/approve")
async def approve_facility(facility_id: int, db: AsyncSession = Depends(get_db)):
    """
    Step 2: Operator verifies GST and Authorized Signatory, then approves the facility.
    Only approved facilities can post shifts.
    """
    stmt = select(Facility).where(Facility.id == facility_id)
    result = await db.execute(stmt)
    facility = result.scalar_one_or_none()
    
    if not facility:
        raise HTTPException(status_code=404, detail="Facility not found")
        
    if not facility.gst_number:
        raise HTTPException(status_code=400, detail="Facility must be claimed before approval")
        
    facility.is_verified = True
    facility.verified_at = datetime.utcnow().isoformat()
    
    await db.commit()
    
    return {
        "message": "Facility verified and approved to post shifts.",
        "facility_id": facility.id,
        "facility_name": facility.name,
        "status": "verified"
    }
