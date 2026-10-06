from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date
from app.models.doctor_master_record import DocumentType

class DoctorOnboardingRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str = Field(..., pattern=r"^\d{10}$", description="10-digit mobile number")
    date_of_birth: Optional[date] = None
    mbbs_university: Optional[str] = None
    mbbs_year: Optional[int] = None
    pg_degree: Optional[str] = None
    pg_specialty: Optional[str] = None

class DoctorOnboardingResponse(BaseModel):
    id: int
    doctor_code: str
    full_name: str
    status: str
    message: str

class DocumentUploadResponse(BaseModel):
    id: int
    doctor_id: int
    document_type: str
    file_name: str
    storage_key: str
    checksum_sha256: str
