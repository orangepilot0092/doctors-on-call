"""
Doctor Master Record — The foundation of DOCTORS ON CALL's trust network.

This schema implements the "Doctor Verification Master Record" with full evidence trail.
Every verification creates an immutable event in the verification_events ledger.

Design Principles:
1. Doctor table = profile information (who the doctor is)
2. DoctorCredential table = individual credentials (what they hold)
3. DoctorDocument table = uploaded files (evidence artifacts)
4. VerificationEvent table = immutable audit ledger (what was checked, by whom, when)

NEVER DELETE FROM verification_events. Only add new events.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import enum


# ─────────────────────────────────────────────────────────────
# ENUMS — Status Definitions from DOCTOR_VERIFICATION_POLICY.md
# ─────────────────────────────────────────────────────────────

class DoctorStatus(str, enum.Enum):
    """Doctor status as defined in DOCTOR_VERIFICATION_POLICY.md"""
    REGISTERED = "registered"      # 🟡 Account created, verification incomplete
    VERIFIED = "verified"          # 🟢 All credentials checked and approved
    SHIFT_READY = "shift_ready"    # 🔵 Verified + operationally ready
    SUSPENDED = "suspended"        # 🔴 Temporarily deactivated
    EXPIRED = "expired"            # ⚫ Verification lapsed
    REJECTED = "rejected"          # ❌ Permanently denied


class VerificationType(str, enum.Enum):
    """Types of verification as per VERIFICATION_SOP.md (14 points)"""
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


class VerificationResult(str, enum.Enum):
    """Result of a verification check"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class DocumentType(str, enum.Enum):
    """Types of documents a doctor can upload"""
    IDENTITY_AADHAAR = "identity_aadhaar"
    IDENTITY_PAN = "identity_pan"
    IDENTITY_PASSPORT = "identity_passport"
    IDENTITY_DRIVING_LICENSE = "identity_driving_license"
    REGISTRATION_CERTIFICATE = "registration_certificate"
    MBBS_CERTIFICATE = "mbbs_certificate"
    PG_CERTIFICATE = "pg_certificate"
    EXPERIENCE_CERTIFICATE = "experience_certificate"
    SPECIALIZATION_CERTIFICATE = "specialization_certificate"
    PROFILE_PHOTO = "profile_photo"
    SELFIE = "selfie"
    DECLARATION = "declaration"
    BANK_DETAILS = "bank_details"
    OTHER = "other"


# ─────────────────────────────────────────────────────────────
# CORE DOCTOR TABLE
# ─────────────────────────────────────────────────────────────

class Doctor(Base):
    """
    Core doctor record — the "source of truth" for doctor information.
    
    This is the doctor's profile. Verification status is tracked
    in verification_events, not here.
    """
    __tablename__ = "doctors"
    
    # Core identity
    id = Column(Integer, primary_key=True, index=True)
    doctor_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g., "DOC-00001"
    
    # Basic information
    full_name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    
    # Current status (computed from verification_events)
    status = Column(SQLEnum(DoctorStatus), nullable=False, default=DoctorStatus.REGISTERED, index=True)
    
    # Trust score (separate from credential status)
    # 0-100, null if not yet calculated
    trust_score = Column(Integer, nullable=True)
    
    # Medical registration summary (denormalized for quick access)
    registration_number = Column(String(100), nullable=True, index=True)
    registration_authority = Column(String(200), nullable=True)
    registration_status = Column(String(50), nullable=True)
    registration_expiry = Column(DateTime, nullable=True)
    
    # Qualifications summary
    mbbs_university = Column(String(200), nullable=True)
    mbbs_year = Column(Integer, nullable=True)
    pg_degree = Column(String(50), nullable=True)  # MD, MS, DNB, etc.
    pg_specialty = Column(String(100), nullable=True)
    pg_institution = Column(String(200), nullable=True)
    
    # Contact & emergency
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)
    
    # Availability
    is_available = Column(Boolean, default=False)
    preferred_locations = Column(JSON, nullable=True)  # List of areas
    preferred_shifts = Column(JSON, nullable=True)  # List of shift types
    availability_notes = Column(Text, nullable=True)
    
    # Bank details (encrypted)
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(100), nullable=True)  # Store encrypted
    bank_ifsc_code = Column(String(20), nullable=True)
    bank_holder_name = Column(String(200), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_verification_at = Column(DateTime(timezone=True), nullable=True)
    status_changed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    credentials = relationship("DoctorCredential", back_populates="doctor", cascade="all, delete-orphan")
    verification_events = relationship("VerificationEvent", back_populates="doctor", cascade="all, delete-orphan")
    documents = relationship("DoctorDocument", back_populates="doctor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Doctor {self.doctor_code} ({self.status.value})>"


# ─────────────────────────────────────────────────────────────
# CREDENTIALS TABLE
# ─────────────────────────────────────────────────────────────

class DoctorCredential(Base):
    """
    Individual credential record — one row per credential type.
    
    Example: A doctor has separate rows for:
    - Medical registration (MMC)
    - MBBS degree
    - MD Anesthesia
    - etc.
    """
    __tablename__ = "doctor_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    
    # Credential type
    credential_type = Column(String(50), nullable=False)  # "medical_registration", "mbbs", "md", etc.
    
    # Credential details
    credential_number = Column(String(100), nullable=True)  # Registration number, roll number, etc.
    issuing_authority = Column(String(200), nullable=True)  # MMC, NMC, University name, etc.
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)  # Operator name or "system"
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)  # Flexible field for credential-specific data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="credentials")
    
    def __repr__(self):
        return f"<DoctorCredential {self.credential_type} for Doctor {self.doctor_id}>"


# ─────────────────────────────────────────────────────────────
# DOCUMENTS TABLE
# ─────────────────────────────────────────────────────────────

class DoctorDocument(Base):
    """
    Document record — tracks uploaded documents with evidence trail.
    
    Actual files stored in Cloudflare R2, not in database.
    Database stores only metadata and reference.
    """
    __tablename__ = "doctor_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    
    # Document metadata
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False)  # R2 object key
    checksum_sha256 = Column(String(64), nullable=False)  # For tamper detection
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # OCR results (if applicable)
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Integer, nullable=True)  # 0-100
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    doctor = relationship("Doctor", back_populates="documents")
    
    def __repr__(self):
        return f"<DoctorDocument {self.document_type.value} for Doctor {self.doctor_id}>"


# ─────────────────────────────────────────────────────────────
# VERIFICATION EVENTS TABLE (IMMUTABLE AUDIT LEDGER)
# ─────────────────────────────────────────────────────────────

class VerificationEvent(Base):
    """
    Immutable audit ledger — every verification action creates a row here.
    
    This is the "evidence trail" that answers:
    "Why do we believe Doctor #DOC-00001 is genuine?"
    
    NEVER DELETE ROWS. Only add new events.
    """
    __tablename__ = "verification_events"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)
    
    # What was verified
    verification_type = Column(SQLEnum(VerificationType), nullable=False)
    
    # Result
    result = Column(SQLEnum(VerificationResult), nullable=False)
    
    # Who verified
    verified_by = Column(String(100), nullable=False)  # Operator name, "system", or "auto"
    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Evidence
    evidence_reference = Column(String(500), nullable=True)  # Document ID, screenshot URL, etc.
    evidence_hash = Column(String(64), nullable=True)  # SHA256 of evidence
    source_url = Column(String(500), nullable=True)  # If checked against online source
    source_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    red_flags = Column(JSON, nullable=True)  # List of red flags identified
    
    # Status change (if this event triggered a status change)
    old_status = Column(SQLEnum(DoctorStatus), nullable=True)
    new_status = Column(SQLEnum(DoctorStatus), nullable=True)
    
    # Expiry (for time-bound verifications)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    doctor = relationship("Doctor", back_populates="verification_events")
    
    def __repr__(self):
        return f"<VerificationEvent {self.verification_type.value} for Doctor {self.doctor_id}: {self.result.value}>"
