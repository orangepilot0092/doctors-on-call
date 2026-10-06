
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.doctor_master_record import Doctor, VerificationEvent, VerificationResult
from app.models.shift import Shift, ShiftStatus
from app.models.dispute import Dispute
from app.models.trust_snapshot import TrustSnapshot
from app.services.ops_events import publish_ops_event


class TrustScoreService:
    BASE_SCORE = 50.0

    @staticmethod
    async def calculate_and_store(db: AsyncSession, doctor_id: int) -> dict:
        doctor = (
            await db.execute(select(Doctor).where(Doctor.id == doctor_id))
        ).scalar_one_or_none()

        if not doctor:
            raise ValueError("Doctor not found")

        # 1. Completed shifts
        completed_shifts = (
            await db.execute(
                select(func.count(Shift.id)).where(
                    Shift.assigned_doctor_id == doctor_id,
                    Shift.status == ShiftStatus.COMPLETED,
                )
            )
        ).scalar() or 0

        # 2. No-show disputes
        no_shows = (
            await db.execute(
                select(func.count(Dispute.id)).where(
                    Dispute.doctor_id == doctor_id,
                    Dispute.dispute_type == "NO_SHOW",
                )
            )
        ).scalar() or 0

        # 3. Late check-ins: check_in_time after shift start_time
        late_check_ins = (
            await db.execute(
                select(func.count(Shift.id)).where(
                    Shift.assigned_doctor_id == doctor_id,
                    Shift.check_in_time.isnot(None),
                    Shift.check_in_time > Shift.start_time,
                )
            )
        ).scalar() or 0

        # 4. Open or under-review disputes
        open_disputes = (
            await db.execute(
                select(func.count(Dispute.id)).where(
                    Dispute.doctor_id == doctor_id,
                    Dispute.status.in_(["OPEN", "UNDER_REVIEW"]),
                )
            )
        ).scalar() or 0

        # 5. Refunded disputes
        refunded_disputes = (
            await db.execute(
                select(func.count(Dispute.id)).where(
                    Dispute.doctor_id == doctor_id,
                    Dispute.status.in_(["REFUNDED", "PARTIAL_REFUND"]),
                )
            )
        ).scalar() or 0

        # 6. Verification approvals
        verification_approved = (
            await db.execute(
                select(func.count(VerificationEvent.id)).where(
                    VerificationEvent.doctor_id == doctor_id,
                    VerificationEvent.result == VerificationResult.APPROVED,
                )
            )
        ).scalar() or 0

        # 7. Verification rejections
        verification_rejected = (
            await db.execute(
                select(func.count(VerificationEvent.id)).where(
                    VerificationEvent.doctor_id == doctor_id,
                    VerificationEvent.result == VerificationResult.REJECTED,
                )
            )
        ).scalar() or 0

        # -----------------------------------------------------
        # Explainable scoring algorithm
        # -----------------------------------------------------
        score = TrustScoreService.BASE_SCORE

        score += min(completed_shifts * 5, 25)
        score += min(verification_approved * 2, 10)

        score -= no_shows * 20
        score -= late_check_ins * 3
        score -= open_disputes * 5
        score -= refunded_disputes * 10
        score -= verification_rejected * 10

        score = max(0.0, min(100.0, score))

        factors = {
            "base_score": TrustScoreService.BASE_SCORE,
            "completed_shifts_bonus": min(completed_shifts * 5, 25),
            "verification_approved_bonus": min(verification_approved * 2, 10),
            "no_show_penalty": no_shows * 20,
            "late_check_in_penalty": late_check_ins * 3,
            "open_dispute_penalty": open_disputes * 5,
            "refunded_dispute_penalty": refunded_disputes * 10,
            "verification_rejected_penalty": verification_rejected * 10,
        }

        explanation_parts = []
        if completed_shifts:
            explanation_parts.append(f"Completed {completed_shifts} shift(s).")
        if verification_approved:
            explanation_parts.append(f"Has {verification_approved} approved verification event(s).")
        if no_shows:
            explanation_parts.append(f"Has {no_shows} no-show dispute(s).")
        if late_check_ins:
            explanation_parts.append(f"Has {late_check_ins} late check-in(s).")
        if open_disputes:
            explanation_parts.append(f"Has {open_disputes} open/under-review dispute(s).")
        if refunded_disputes:
            explanation_parts.append(f"Has {refunded_disputes} refunded dispute(s).")
        if verification_rejected:
            explanation_parts.append(f"Has {verification_rejected} rejected verification event(s).")

        explanation = " ".join(explanation_parts) or "No behavioral trust signals recorded yet."

        now = datetime.now(timezone.utc)

        snapshot = TrustSnapshot(
            doctor_id=doctor_id,
            score=score,
            completed_shifts=completed_shifts,
            no_shows=no_shows,
            late_check_ins=late_check_ins,
            open_disputes=open_disputes,
            refunded_disputes=refunded_disputes,
            verification_approved=verification_approved,
            verification_rejected=verification_rejected,
            factors=factors,
            explanation=explanation,
            calculated_at=now,
        )

        doctor.trust_score = score
        doctor.completed_shift_count = completed_shifts
        doctor.no_show_count = no_shows
        doctor.late_check_in_count = late_check_ins
        doctor.last_trust_calculated_at = now

        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)
        await db.refresh(doctor)

        await publish_ops_event(
            None,
            'TRUST_UPDATED',
            {
                'doctor_id': doctor_id,
                'doctor_name': doctor.full_name,
                'trust_score': score,
                'explanation': explanation,
            },
            channel='global',
        )
        return {
            "doctor_id": doctor_id,
            "doctor_code": doctor.doctor_code,
            "doctor_name": doctor.full_name,
            "trust_score": doctor.trust_score,
            "completed_shifts": completed_shifts,
            "no_shows": no_shows,
            "late_check_ins": late_check_ins,
            "open_disputes": open_disputes,
            "refunded_disputes": refunded_disputes,
            "verification_approved": verification_approved,
            "verification_rejected": verification_rejected,
            "factors": factors,
            "explanation": explanation,
            "snapshot_id": snapshot.id,
            "calculated_at": snapshot.calculated_at.isoformat(),
        }
