"""
Pydantic schemas for the Verification API.

These schemas define the request/response models for:
- Recording verification events
- Updating doctor status
- Retrieving verification history
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ─────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────

class DoctorStatus(str, Enum):
    REGISTERED = "registered"
    VERIFIED = "verified"
    SHIFT_READY = "shift_ready"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REJECTED = "rejected"


class VerificationType(str, Enum):
    # Phase 1: Identity (Points 1-3)
    IDENTITY = "identity"
    NAME_MATCH = "name_match"
    PHOTO_MATCH = "photo_match"
    # Phase 2: Medical Registration (Points 4-7)
    REGISTRATION_NUMBER = "registration_number"
    REGISTRATION_AUTHORITY = "registration_authority"
    REGISTRATION_STATUS = "registration_status"
    DATE_CHECKED = "date_checked"
    # Phase 3: Qualifications (Points 8-10)
    MBBS_CERTIFICATE = "mbbs_certificate"
    PG_QUALIFICATION = "pg_qualification"
    SPECIALIZATION = "specialization"
    # Phase 4: Professional History (Point 11)
    EXPERIENCE = "experience"
    # Phase 5: Administrative (Points 12-14)
    BANK_DETAILS = "bank_details"
    DECLARATION = "declaration"
    ONBOARDING = "onboarding"


class VerificationResult(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


# ─────────────────────────────────────────────────────────────
# VERIFICATION EVENT SCHEMAS
# ─────────────────────────────────────────────────────────────

class VerificationEventCreate(BaseModel):
    """Schema for creating a new verification event"""
    doctor_id: int = Field(..., description="Doctor ID")
    verification_type: VerificationType = Field(..., description="Type of verification performed")
    result: VerificationResult = Field(..., description="Result of verification")
    verified_by: str = Field(..., description="Name of person or system that verified", min_length=1)
    
    # Optional evidence fields
    evidence_reference: Optional[str] = Field(None, description="Reference to evidence (document ID, URL, etc.)")
    evidence_hash: Optional[str] = Field(None, description="SHA256 hash of evidence", min_length=64, max_length=64)
    source_url: Optional[str] = Field(None, description="URL of official source checked")
    
    # Notes and flags
    notes: Optional[str] = Field(None, description="Additional notes from verifier")
    red_flags: Optional[List[str]] = Field(None, description="List of red flags identified")
    
    # Status change (optional)
    new_status: Optional[DoctorStatus] = Field(None, description="New status if this event triggers status change")
    
    # Expiry
    expires_at: Optional[datetime] = Field(None, description="When this verification expires")


class VerificationEventResponse(BaseModel):
    """Schema for verification event response"""
    id: int
    doctor_id: int
    verification_type: VerificationType
    result: VerificationResult
    verified_by: str
    verified_at: datetime
    evidence_reference: Optional[str]
    evidence_hash: Optional[str]
    source_url: Optional[str]
    notes: Optional[str]
    red_flags: Optional[List[str]]
    old_status: Optional[DoctorStatus]
    new_status: Optional[DoctorStatus]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────────
# DOCTOR STATUS SCHEMAS
# ─────────────────────────────────────────────────────────────

class DoctorStatusUpdate(BaseModel):
    """Schema for updating doctor status"""
    new_status: DoctorStatus = Field(..., description="New status for doctor")
    reason: str = Field(..., description="Reason for status change", min_length=1)
    updated_by: str = Field(..., description="Name of person updating status", min_length=1)


class DoctorStatusResponse(BaseModel):
    """Schema for doctor status response"""
    doctor_id: int
    doctor_code: str
    old_status: DoctorStatus
    new_status: DoctorStatus
    updated_at: datetime
    updated_by: str
    reason: str


# ─────────────────────────────────────────────────────────────
# DOCTOR PROFILE SCHEMAS
# ─────────────────────────────────────────────────────────────

class DoctorProfileResponse(BaseModel):
    """Schema for doctor profile with verification summary"""
    id: int
    doctor_code: str
    full_name: str
    email: str
    phone: str
    status: DoctorStatus
    trust_score: Optional[int]
    
    # Registration summary
    registration_number: Optional[str]
    registration_authority: Optional[str]
    registration_status: Optional[str]
    registration_expiry: Optional[datetime]
    
    # Qualifications summary
    mbbs_university: Optional[str]
    mbbs_year: Optional[int]
    pg_degree: Optional[str]
    pg_specialty: Optional[str]
    
    # Availability
    is_available: bool
    preferred_locations: Optional[List[str]]
    
    # Timestamps
    created_at: datetime
    last_verification_at: Optional[datetime]
    status_changed_at: Optional[datetime]
    
    # Verification summary
    verification_count: int = Field(..., description="Total number of verification events")
    approved_count: int = Field(..., description="Number of approved verifications")
    rejected_count: int = Field(..., description="Number of rejected verifications")
    pending_count: int = Field(..., description="Number of pending verifications")
    
    class Config:
        from_attributes = True


class DoctorListResponse(BaseModel):
    """Schema for listing doctors with filters"""
    total: int
    doctors: List[DoctorProfileResponse]


class VerificationHistoryResponse(BaseModel):
    """Schema for doctor verification history"""
    doctor_id: int
    doctor_code: str
    doctor_name: str
    current_status: DoctorStatus
    events: List[VerificationEventResponse]
