from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.db.base import Base

class HospitalAdmin(Base):
    __tablename__ = "hospital_admins"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.id"), nullable=False)
    is_active = Column(Boolean, default=True)
