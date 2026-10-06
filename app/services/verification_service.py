"""
Verification Service — Business logic for doctor verification.

This service handles:
- Recording verification events
- Updating doctor status
- Retrieving verification history
- Calculating verification statistics
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from datetime import datetime

from app.models.doctor_master_record import (
    Doctor,
    DoctorCredential,
    DoctorDocument,
    VerificationEvent,
    DoctorStatus,
    VerificationType,
    VerificationResult,
)
from app.schemas.verification import (
    VerificationEventCreate,
    DoctorStatusUpdate,
)


class VerificationService:
    """Service for managing doctor verification"""
    
    @staticmethod
    async def create_verification_event(
        db: AsyncSession,
        event_data: VerificationEventCreate
    ) -> VerificationEvent:
        """
        Create a new verification event.
        
        If new_status is provided, also update the doctor's status.
        """
        # Get doctor to capture old status
        result = await db.execute(
            select(Doctor).where(Doctor.id == event_data.doctor_id)
        )
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise ValueError(f"Doctor with ID {event_data.doctor_id} not found")
        
        old_status = doctor.status
        
        # Create verification event
        event = VerificationEvent(
            doctor_id=event_data.doctor_id,
            verification_type=event_data.verification_type,
            result=event_data.result,
            verified_by=event_data.verified_by,
            evidence_reference=event_data.evidence_reference,
            evidence_hash=event_data.evidence_hash,
            source_url=event_data.source_url,
            notes=event_data.notes,
            red_flags=event_data.red_flags,
            old_status=old_status,
            new_status=event_data.new_status,
            expires_at=event_data.expires_at,
        )
        
        db.add(event)
        
        # Update doctor status if provided
        if event_data.new_status:
            doctor.status = event_data.new_status
            doctor.status_changed_at = datetime.utcnow()
            doctor.last_verification_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(event)
        
        return event
    
    @staticmethod
    async def update_doctor_status(
        db: AsyncSession,
        doctor_id: int,
        status_update: DoctorStatusUpdate
    ) -> Doctor:
        """
        Update doctor status with audit trail.
        
        This creates a verification event of type DATE_CHECKED to record the change.
        """
        # Get doctor
        result = await db.execute(
            select(Doctor).where(Doctor.id == doctor_id)
        )
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise ValueError(f"Doctor with ID {doctor_id} not found")
        
        old_status = doctor.status
        
        # Create audit event
        event = VerificationEvent(
            doctor_id=doctor_id,
            verification_type=VerificationType.DATE_CHECKED,
            result=VerificationResult.APPROVED,
            verified_by=status_update.updated_by,
            notes=f"Status changed: {old_status.value} -> {status_update.new_status.value}. Reason: {status_update.reason}",
            old_status=old_status,
            new_status=status_update.new_status,
        )
        
        db.add(event)
        
        # Update doctor status
        doctor.status = status_update.new_status
        doctor.status_changed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(doctor)
        
        return doctor
    
    @staticmethod
    async def get_doctor_profile(
        db: AsyncSession,
        doctor_id: int
    ) -> Tuple[Doctor, dict]:
        """
        Get doctor profile with verification statistics.
        
        Returns doctor object and verification stats dict.
        """
        # Get doctor with related data
        result = await db.execute(
            select(Doctor)
            .where(Doctor.id == doctor_id)
            .options(selectinload(Doctor.verification_events))
        )
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise ValueError(f"Doctor with ID {doctor_id} not found")
        
        # Calculate verification statistics
        events = doctor.verification_events
        total = len(events)
        approved = sum(1 for e in events if e.result == VerificationResult.APPROVED)
        rejected = sum(1 for e in events if e.result == VerificationResult.REJECTED)
        pending = sum(1 for e in events if e.result == VerificationResult.PENDING)
        
        stats = {
            "verification_count": total,
            "approved_count": approved,
            "rejected_count": rejected,
            "pending_count": pending,
        }
        
        return doctor, stats
    
    @staticmethod
    async def get_verification_history(
        db: AsyncSession,
        doctor_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[Doctor, List[VerificationEvent]]:
        """
        Get doctor's verification history.
        
        Returns doctor object and list of verification events.
        """
        # Get doctor
        result = await db.execute(
            select(Doctor).where(Doctor.id == doctor_id)
        )
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise ValueError(f"Doctor with ID {doctor_id} not found")
        
        # Get verification events (most recent first)
        result = await db.execute(
            select(VerificationEvent)
            .where(VerificationEvent.doctor_id == doctor_id)
            .order_by(VerificationEvent.verified_at.desc())
            .limit(limit)
            .offset(offset)
        )
        events = result.scalars().all()
        
        return doctor, events
    
    @staticmethod
    async def list_doctors(
        db: AsyncSession,
        status: Optional[DoctorStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[int, List[Doctor]]:
        """
        List doctors with optional status filter.
        
        Returns total count and list of doctors.
        """
        # Build query
        query = select(Doctor).options(selectinload(Doctor.verification_events))
        
        if status:
            query = query.where(Doctor.status == status)
        
        # Get total count
        count_query = select(func.count(Doctor.id))
        if status:
            count_query = count_query.where(Doctor.status == status)
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # Get doctors (most recent first)
        query = query.order_by(Doctor.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        doctors = result.scalars().all()
        
        return total, doctors


# Instantiate service
verification_service = VerificationService()
