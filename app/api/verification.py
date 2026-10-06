"""
Verification API Router — Endpoints for managing doctor verification.

Endpoints:
- POST /api/v1/verification/events — Record a verification event
- GET /api/v1/verification/doctors/{doctor_id}/history — Get verification history
- PATCH /api/v1/verification/doctors/{doctor_id}/status — Update doctor status
- GET /api/v1/verification/doctors/{doctor_id}/profile — Get doctor profile with stats
- GET /api/v1/verification/doctors — List doctors with filters
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.db.session import get_db
from app.services.verification_service import verification_service
from app.schemas.verification import (
    VerificationEventCreate,
    VerificationEventResponse,
    DoctorStatusUpdate,
    DoctorStatusResponse,
    DoctorProfileResponse,
    DoctorListResponse,
    VerificationHistoryResponse,
    DoctorStatus,
)

router = APIRouter(prefix="/verification", tags=["Doctor Verification"])


# ─────────────────────────────────────────────────────────────
# VERIFICATION EVENT ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post("/events", response_model=VerificationEventResponse, status_code=201)
async def create_verification_event(
    event_data: VerificationEventCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Record a new verification event.
    
    Use this endpoint to record each of the 14 verification points:
    - Identity verification (points 1-3)
    - Medical registration (points 4-7)
    - Qualifications (points 8-10)
    - Experience (point 11)
    - Administrative (points 12-14)
    
    Example:
    ```json
    {
        "doctor_id": 1,
        "verification_type": "registration_number",
        "result": "approved",
        "verified_by": "John Doe",
        "source_url": "https://mmcouncil.com/doctor-search/",
        "notes": "Registration number verified against MMC database"
    }
    ```
    """
    try:
        event = await verification_service.create_verification_event(db, event_data)
        return event
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create verification event: {str(e)}")


# ─────────────────────────────────────────────────────────────
# DOCTOR STATUS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.patch("/doctors/{doctor_id}/status", response_model=DoctorStatusResponse)
async def update_doctor_status(
    doctor_id: int,
    status_update: DoctorStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update doctor status with audit trail.
    
    Status transitions allowed:
    - registered → verified (after all 14 points completed)
    - verified → shift_ready (after availability confirmed)
    - any → suspended (red flag raised)
    - suspended → verified (issue resolved)
    - any → rejected (fraud detected)
    
    Example:
    ```json
    {
        "new_status": "verified",
        "reason": "All 14 verification points completed successfully",
        "updated_by": "Senior Verification Officer"
    }
    ```
    """
    try:
        doctor = await verification_service.update_doctor_status(db, doctor_id, status_update)
        return {
            "doctor_id": doctor.id,
            "doctor_code": doctor.doctor_code,
            "old_status": status_update.new_status,  # This will be updated in service
            "new_status": doctor.status,
            "updated_at": doctor.status_changed_at,
            "updated_by": status_update.updated_by,
            "reason": status_update.reason,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update doctor status: {str(e)}")


# ─────────────────────────────────────────────────────────────
# DOCTOR PROFILE ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/doctors/{doctor_id}/profile", response_model=DoctorProfileResponse)
async def get_doctor_profile(
    doctor_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get doctor profile with verification statistics.
    
    Returns:
    - Doctor basic information
    - Current status
    - Registration summary
    - Qualifications summary
    - Verification counts (total, approved, rejected, pending)
    """
    try:
        doctor, stats = await verification_service.get_doctor_profile(db, doctor_id)
        return {
            **doctor.__dict__,
            **stats,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get doctor profile: {str(e)}")


@router.get("/doctors/{doctor_id}/history", response_model=VerificationHistoryResponse)
async def get_verification_history(
    doctor_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Get doctor's complete verification history.
    
    Returns all verification events in reverse chronological order (most recent first).
    This is the immutable audit trail that answers: "Why do we trust this doctor?"
    """
    try:
        doctor, events = await verification_service.get_verification_history(
            db, doctor_id, limit, offset
        )
        return {
            "doctor_id": doctor.id,
            "doctor_code": doctor.doctor_code,
            "doctor_name": doctor.full_name,
            "current_status": doctor.status,
            "events": events,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get verification history: {str(e)}")


@router.get("/doctors", response_model=DoctorListResponse)
async def list_doctors(
    status: Optional[DoctorStatus] = Query(None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List doctors with optional status filter.
    
    Use this endpoint to:
    - View all registered doctors (status=registered)
    - View all verified doctors (status=verified)
    - View all shift-ready doctors (status=shift_ready)
    - View all suspended doctors (status=suspended)
    """
    try:
        total, doctors = await verification_service.list_doctors(db, status, limit, offset)
        
        doctor_profiles = []
        for doctor in doctors:
            # Calculate verification stats
            events = doctor.verification_events
            stats = {
                "verification_count": len(events),
                "approved_count": sum(1 for e in events if e.result == "approved"),
                "rejected_count": sum(1 for e in events if e.result == "rejected"),
                "pending_count": sum(1 for e in events if e.result == "pending"),
            }
            
            doctor_profiles.append({
                **doctor.__dict__,
                **stats,
            })
        
        return {
            "total": total,
            "doctors": doctor_profiles,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list doctors: {str(e)}")
