from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class HPRProfile(Base):
    __tablename__ = "hpr_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # ABDM Core Identifiers
    hpr_id = Column(String, unique=True, index=True, nullable=True)  # e.g., "71-XXXX-XXXX-XXXX"
    hpr_token = Column(String, nullable=True)  # JWT from ABDM Login
    token_expires_at = Column(String, nullable=True)
    
    # Verification Status (From Fetch Professional Details API)
    is_council_verified = Column(String, default="Pending")  # Submitted, Verified, Rejected
    is_work_verified = Column(String, default="Pending")
    application_status = Column(String, default="Draft")
    
    # Cached Professional Data (JSON for flexibility, can be normalized later)
    council_name = Column(String, nullable=True)  # e.g., "Maharashtra Medical Council"
    registration_number = Column(String, nullable=True)
    qualification_details = Column(JSON, nullable=True)
    work_details = Column(JSON, nullable=True)
    
    user = relationship("User", back_populates="hpr_profile")

# Add relationship to User
from app.models.user import User
User.hpr_profile = relationship("HPRProfile", back_populates="user", uselist=False)
