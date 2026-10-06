from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class TrustSnapshot(Base):
    __tablename__ = "trust_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)

    score = Column(Float, nullable=False, index=True)

    completed_shifts = Column(Integer, nullable=False, default=0)
    no_shows = Column(Integer, nullable=False, default=0)
    late_check_ins = Column(Integer, nullable=False, default=0)

    open_disputes = Column(Integer, nullable=False, default=0)
    refunded_disputes = Column(Integer, nullable=False, default=0)

    verification_approved = Column(Integer, nullable=False, default=0)
    verification_rejected = Column(Integer, nullable=False, default=0)

    factors = Column(JSON, nullable=True)
    explanation = Column(String, nullable=True)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
