from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import json

from app.db.database import get_db
from app.models.doctor import Doctor, VerificationStatus
from app.models.shift import ShiftRequest, ShiftStatus
from app.schemas.doctor import DoctorCreateRequest, DoctorResponse
from app.services.whatsapp import send_shift_offer_to_doctor
from app.services.ai_verification import ai_verifier

router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors"])


@router.post("/register-with-document")
async def register_doctor_with_document(
    name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    specialization: str = Form(...),
    base_location: str = Form(...),
    pincode: str = Form(...),
    daily_rate: float = Form(3500.0),
    preferred_zones: Optional[str] = Form(None),
    availability_calendar: Optional[str] = Form(None),
    certificate: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Register doctor with AI-powered document verification.
    Upload NMC certificate and let AI extract & verify automatically.
    """
    # Check if phone already exists
    existing = await db.execute(select(Doctor).where(Doctor.phone == phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    # Read uploaded file
    file_content = await certificate.read()
    
    # Run AI verification
    print(f"\n🤖 Running AI verification for {name}...")
    verification_result = await ai_verifier.full_verification_workflow(
        file_content, 
        certificate.filename
    )
    
    # Extract registration number from AI result
    nmc_registration = None
    if verification_result.get("success"):
        extraction = verification_result.get("extraction", {})
        nmc_registration = extraction.get("registration_number")
    
    # Parse JSON fields
    preferred_zones_list = json.loads(preferred_zones) if preferred_zones else None
    availability_dict = json.loads(availability_calendar) if availability_calendar else {}
    
    # Create doctor record
    new_doctor = Doctor(
        name=name,
        phone=phone,
        email=email,
        specialization=specialization,
        nmc_registration=nmc_registration,
        base_location=base_location,
        pincode=pincode,
        preferred_zones=preferred_zones_list,
        daily_rate=daily_rate,
        availability_calendar=availability_dict,
        verification_status=VerificationStatus.PENDING  # Always pending until manual review
    )
    db.add(new_doctor)
    await db.commit()
    await db.refresh(new_doctor)
    
    # Prepare response
    response = {
        "doctor_id": str(new_doctor.id),
        "name": new_doctor.name,
        "phone": new_doctor.phone,
        "verification_status": new_doctor.verification_status.value,
        "ai_verification": verification_result,
        "message": "Registration successful! AI verification completed. Awaiting manual review."
    }
    
    return response


@router.post("/register", response_model=DoctorResponse)
async def register_doctor(
    request: DoctorCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new doctor (without document upload)."""
    existing = await db.execute(select(Doctor).where(Doctor.phone == request.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    new_doctor = Doctor(
        name=request.name,
        phone=request.phone,
        email=request.email,
        specialization=request.specialization,
        nmc_registration=request.nmc_registration,
        base_location=request.base_location,
        pincode=request.pincode,
        preferred_zones=request.preferred_zones,
        daily_rate=request.daily_rate,
        availability_calendar=request.availability_calendar or {},
    )
    db.add(new_doctor)
    await db.commit()
    await db.refresh(new_doctor)

    return DoctorResponse(
        id=new_doctor.id,
        name=new_doctor.name,
        specialization=new_doctor.specialization,
        verification_status=new_doctor.verification_status.value,
        message="Registration successful! We will verify your credentials within 24 hours."
    )


@router.get("/list", response_model=List[DoctorResponse])
async def list_doctors(
    verification_status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List all doctors (admin view)."""
    query = select(Doctor).order_by(Doctor.created_at.desc())
    if verification_status:
        query = query.where(Doctor.verification_status == VerificationStatus(verification_status))
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    return [
        DoctorResponse(
            id=d.id,
            name=d.name,
            specialization=d.specialization,
            verification_status=d.verification_status.value,
            phone=d.phone,
            base_location=d.base_location,
            daily_rate=float(d.daily_rate)
        )
        for d in doctors
    ]


@router.post("/{doctor_id}/verify")
async def verify_doctor(
    doctor_id: uuid.UUID,
    status: str,
    db: AsyncSession = Depends(get_db)
):
    """Manually verify/reject a doctor's credentials."""
    result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
    doctor = result.scalar_one_or_none()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    doctor.verification_status = VerificationStatus(status)
    await db.commit()
    
    return {"message": f"Doctor {doctor.name} marked as {status}"}


@router.get("/available-for-shift")
async def find_available_doctors(
    specialty: str,
    shift_date: str,
    pincode: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Find verified doctors available for a specific shift."""
    query = select(Doctor).where(
        Doctor.verification_status == VerificationStatus.VERIFIED,
        Doctor.is_active == True,
        Doctor.specialization.ilike(f"%{specialty}%")
    )
    
    if pincode:
        query = query.where(Doctor.pincode == pincode)
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    available_doctors = []
    for doc in doctors:
        if doc.availability_calendar and doc.availability_calendar.get(shift_date) == "free":
            available_doctors.append(doc)
        elif not doc.availability_calendar:
            available_doctors.append(doc)
    
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "phone": d.phone,
            "specialization": d.specialization,
            "base_location": d.base_location,
            "daily_rate": float(d.daily_rate),
            "match_score": 0.95
        }
        for d in available_doctors
    ]


@router.post("/notify-doctors")
async def notify_available_doctors(
    shift_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Send WhatsApp notifications to available doctors for a shift."""
    shift_result = await db.execute(select(ShiftRequest).where(ShiftRequest.id == shift_id))
    shift = shift_result.scalar_one_or_none()
    
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    
    query = select(Doctor).where(
        Doctor.verification_status == VerificationStatus.VERIFIED,
        Doctor.is_active == True,
        Doctor.specialization.ilike(f"%{shift.specialty}%")
    )
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    notified_count = 0
    for doc in doctors:
        if doc.availability_calendar and doc.availability_calendar.get(shift.shift_date) == "busy":
            continue
        
        success = await send_shift_offer_to_doctor(
            doctor_phone=doc.phone,
            doctor_name=doc.name,
            clinic_name=shift.clinic_name,
            location=shift.clinic_pincode,
            specialty=shift.specialty,
            shift_date=shift.shift_date,
            shift_time=shift.shift_time,
            payout=float(doc.daily_rate)
        )
        
        if success:
            notified_count += 1
            shift.doctors_contacted_count = (shift.doctors_contacted_count or 0) + 1
    
    await db.commit()
    
    return {
        "message": f"Notified {notified_count} doctors via WhatsApp",
        "shift_id": str(shift.id),
        "doctors_notified": notified_count
    }
