import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.doctor_master_record import (
    Doctor, DoctorDocument, VerificationEvent, 
    DoctorStatus, DocumentType, VerificationType, VerificationResult
)
from app.core.storage import storage_client
from app.core.ocr import ocr_client
from app.schemas.onboarding import DoctorOnboardingRequest

DOC_TYPE_TO_VERIFICATION_TYPE = {
    DocumentType.IDENTITY_AADHAAR: VerificationType.IDENTITY,
    DocumentType.IDENTITY_PAN: VerificationType.IDENTITY,
    DocumentType.IDENTITY_PASSPORT: VerificationType.IDENTITY,
    DocumentType.IDENTITY_DRIVING_LICENSE: VerificationType.IDENTITY,
    DocumentType.REGISTRATION_CERTIFICATE: VerificationType.REGISTRATION_NUMBER,
    DocumentType.MBBS_CERTIFICATE: VerificationType.MBBS_CERTIFICATE,
    DocumentType.PG_CERTIFICATE: VerificationType.PG_QUALIFICATION,
    DocumentType.EXPERIENCE_CERTIFICATE: VerificationType.EXPERIENCE,
    DocumentType.PROFILE_PHOTO: VerificationType.PHOTO_MATCH,
    DocumentType.DECLARATION: VerificationType.DECLARATION,
}

async def get_next_doctor_code(db: AsyncSession) -> str:
    result = await db.execute(select(func.max(Doctor.id)))
    max_id = result.scalar() or 0
    return f"DOC-{str(max_id + 1).zfill(5)}"

async def onboard_doctor(db: AsyncSession, data: DoctorOnboardingRequest) -> Doctor:
    doctor_code = await get_next_doctor_code(db)
    doctor = Doctor(
        doctor_code=doctor_code,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        mbbs_university=data.mbbs_university,
        mbbs_year=data.mbbs_year,
        pg_degree=data.pg_degree,
        pg_specialty=data.pg_specialty,
        status=DoctorStatus.REGISTERED
    )
    db.add(doctor)
    await db.commit()
    await db.refresh(doctor)
    return doctor

async def upload_doctor_document(
    db: AsyncSession, 
    doctor_id: int, 
    file_bytes: bytes, 
    file_name: str, 
    content_type: str, 
    doc_type: DocumentType
) -> DoctorDocument:
    
    # 1. Upload to Object Storage
    storage_key = storage_client.upload_file(file_bytes, file_name, content_type)
    
    # 2. Calculate SHA256 for tamper detection
    checksum = hashlib.sha256(file_bytes).hexdigest()
    
    # 3. 🆕 Run Automated OCR
    ocr_text, ocr_conf = ocr_client.extract_text(file_bytes, content_type)
    
    # 4. Save document record to DB
    doc = DoctorDocument(
        doctor_id=doctor_id,
        document_type=doc_type,
        file_name=file_name,
        storage_key=storage_key,
        checksum_sha256=checksum,
        file_size_bytes=len(file_bytes),
        mime_type=content_type,
        ocr_text=ocr_text,
        ocr_confidence=ocr_conf,
        is_verified=False
    )
    db.add(doc)
    
    # 5. Create PENDING verification event
    verification_type = DOC_TYPE_TO_VERIFICATION_TYPE.get(doc_type, VerificationType.IDENTITY)
    
    event = VerificationEvent(
        doctor_id=doctor_id,
        verification_type=verification_type,
        result=VerificationResult.PENDING,
        verified_by="system",
        notes=f"Document uploaded. OCR Confidence: {ocr_conf}%",
        evidence_reference=storage_key
    )
    db.add(event)
    
    await db.commit()
    await db.refresh(doc)
    return doc
