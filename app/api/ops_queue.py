from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from pydantic import BaseModel
from app.db.session import get_db
from app.models.doctor_master_record import (
    Doctor, DoctorDocument, VerificationEvent, 
    VerificationResult, VerificationType
)
from app.core.storage import storage_client
from app.services.onboarding_service import DOC_TYPE_TO_VERIFICATION_TYPE

router = APIRouter(prefix="/ops", tags=["Operator Review Queue"])

class QueueItem(BaseModel):
    doctor_id: int
    doctor_code: str
    doctor_name: str
    document_id: int
    document_type: str
    file_name: str
    document_url: str
    uploaded_at: str

@router.get("/queue", response_model=List[QueueItem])
async def get_pending_documents(db: AsyncSession = Depends(get_db)):
    """Fetch all uploaded documents that have NOT yet been verified."""
    stmt = (
        select(DoctorDocument)
        .join(Doctor, DoctorDocument.doctor_id == Doctor.id)
        .where(DoctorDocument.is_verified == False)
        .options(selectinload(DoctorDocument.doctor))
        .order_by(DoctorDocument.uploaded_at.asc())
    )
    result = await db.execute(stmt)
    docs = result.scalars().all()
    
    queue = []
    for doc in docs:
        try:
            url = storage_client.get_presigned_url(doc.storage_key)
        except Exception:
            url = "#error-generating-url"
            
        queue.append(QueueItem(
            doctor_id=doc.doctor_id,
            doctor_code=doc.doctor.doctor_code,
            doctor_name=doc.doctor.full_name,
            document_id=doc.id,
            document_type=doc.document_type.value,
            file_name=doc.file_name,
            document_url=url,
            uploaded_at=doc.uploaded_at.isoformat()
        ))
    return queue

class ReviewRequest(BaseModel):
    verified_by: str
    notes: str

@router.post("/documents/{doc_id}/approve")
async def approve_document(doc_id: int, data: ReviewRequest, db: AsyncSession = Depends(get_db)):
    """
    Approve a document.
    1. Marks document as verified.
    2. Creates a NEW immutable APPROVED event in the audit ledger.
    """
    stmt = select(DoctorDocument).where(DoctorDocument.id == doc_id).options(selectinload(DoctorDocument.doctor))
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    
    if not doc: raise HTTPException(status_code=404, detail="Document not found")
        
    doc.is_verified = True
    v_type = DOC_TYPE_TO_VERIFICATION_TYPE.get(doc.document_type, VerificationType.IDENTITY)
    
    # Create NEW immutable event (Never update the PENDING event!)
    event = VerificationEvent(
        doctor_id=doc.doctor_id,
        verification_type=v_type,
        result=VerificationResult.APPROVED,
        verified_by=data.verified_by,
        notes=data.notes,
        evidence_reference=doc.storage_key,
        evidence_hash=doc.checksum_sha256
    )
    db.add(event)
    await db.commit()
    return {"status": "approved", "document_id": doc_id}

@router.post("/documents/{doc_id}/reject")
async def reject_document(doc_id: int, data: ReviewRequest, db: AsyncSession = Depends(get_db)):
    """Reject a document and create a REJECTED audit event."""
    stmt = select(DoctorDocument).where(DoctorDocument.id == doc_id).options(selectinload(DoctorDocument.doctor))
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    
    if not doc: raise HTTPException(status_code=404, detail="Document not found")
        
    v_type = DOC_TYPE_TO_VERIFICATION_TYPE.get(doc.document_type, VerificationType.IDENTITY)
    
    event = VerificationEvent(
        doctor_id=doc.doctor_id,
        verification_type=v_type,
        result=VerificationResult.REJECTED,
        verified_by=data.verified_by,
        notes=data.notes,
        evidence_reference=doc.storage_key,
        evidence_hash=doc.checksum_sha256
    )
    db.add(event)
    await db.commit()
    return {"status": "rejected", "document_id": doc_id}
