from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.onboarding_service import onboard_doctor, upload_doctor_document
from app.schemas.onboarding import DoctorOnboardingRequest, DoctorOnboardingResponse, DocumentUploadResponse
from app.models.doctor_master_record import DocumentType

router = APIRouter(prefix="/onboarding", tags=["Doctor Onboarding"])

@router.post("/doctor", response_model=DoctorOnboardingResponse, status_code=201)
async def create_doctor_profile(data: DoctorOnboardingRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 1 of Onboarding: Create the initial doctor profile.
    Status is automatically set to REGISTERED.
    """
    doctor = await onboard_doctor(db, data)
    return {
        "id": doctor.id,
        "doctor_code": doctor.doctor_code,
        "full_name": doctor.full_name,
        "status": doctor.status.value,
        "message": "Profile created. Please upload your documents."
    }

@router.post("/doctors/{doctor_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    doctor_id: int,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2 of Onboarding: Upload identity, registration, or qualification documents.
    Automatically creates a PENDING verification event for the Operator Dashboard.
    """
    contents = await file.read()
    
    # Enforce 5MB limit per VERIFICATION_SOP.md
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
        
    doc = await upload_doctor_document(
        db=db,
        doctor_id=doctor_id,
        file_bytes=contents,
        file_name=file.filename,
        content_type=file.content_type,
        doc_type=document_type
    )
    return doc
