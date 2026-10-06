from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.db.session import get_db
from app.models.doctor_master_record import (
    Doctor, DoctorDocument, VerificationEvent, 
    VerificationType, VerificationResult, DocumentType
)
from app.services.registry_scraper import registry_scraper

router = APIRouter(prefix="/verification", tags=["Registry Verification"])

@router.post("/registry-check/{doctor_id}")
async def check_medical_registry(doctor_id: int, db: AsyncSession = Depends(get_db)):
    """
    Triggers an automated check of the doctor's medical registration number
    against the official NMC/MMC registry and appends the result to the audit ledger.
    """
    # 1. Fetch doctor
    stmt = select(Doctor).where(Doctor.id == doctor_id)
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
        
    # 2. Find the uploaded Registration Certificate and extract the Reg Number from OCR text
    doc_stmt = select(DoctorDocument).where(
        DoctorDocument.doctor_id == doctor_id,
        DoctorDocument.document_type == DocumentType.REGISTRATION_CERTIFICATE
    )
    doc_result = await db.execute(doc_stmt)
    reg_doc = doc_result.scalars().first()
    
    reg_number = None
    if reg_doc and reg_doc.ocr_text:
        # Regex to find patterns like MMC-123456 or NMC-987654
        match = re.search(r'(MMC|NMC|DMC|KMC)[-\s]?\d{4,6}', reg_doc.ocr_text, re.IGNORECASE)
        if match:
            reg_number = match.group(0).replace(" ", "").upper()
            
    if not reg_number:
        raise HTTPException(status_code=400, detail="Could not extract registration number from uploaded documents via OCR.")

    # 3. Query the registry
    registry_result = await registry_scraper.verify_registration(reg_number)
    
    # 4. Create immutable audit event based on registry response
    if registry_result["found"] and registry_result["data"]["status"] == "active":
        event_result = VerificationResult.APPROVED
        notes = f"Registry check PASSED for {reg_number}. Name: {registry_result['data']['name']}, Status: Active. Source: {registry_result['source']}"
    elif registry_result["found"] and registry_result["data"]["status"] != "active":
        event_result = VerificationResult.REJECTED
        notes = f"Registry check FAILED for {reg_number}. Status is {registry_result['data']['status']}. Source: {registry_result['source']}"
    else:
        event_result = VerificationResult.REJECTED
        notes = f"Registry check FAILED for {reg_number}. Number not found in official registry. Source: {registry_result['source']}"
        
    event = VerificationEvent(
        doctor_id=doctor_id,
        verification_type=VerificationType.REGISTRATION_STATUS,
        result=event_result,
        verified_by="system_registry_scraper",
        notes=notes,
        source_url="https://nmc.org.in/medical-information-registry/indian-medical-register/"
    )
    db.add(event)
    await db.commit()
    
    return {"status": event_result.value, "reg_number": reg_number, "details": notes}
