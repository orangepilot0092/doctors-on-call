
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.shift import Shift, ShiftStatus
from app.models.dispute import Dispute
from app.models.ledger import LedgerEntry
from app.services.ops_events import publish_ops_event


class DisputeService:
    @staticmethod
    async def open_dispute(
        db: AsyncSession,
        shift_id: int,
        dispute_type: str,
        doctor_id: int | None = None,
        hospital_id: int | None = None,
        amount_claimed: float | None = None,
        notes: str | None = None,
    ) -> Dispute:
        shift = (
            await db.execute(select(Shift).where(Shift.id == shift_id))
        ).scalar_one_or_none()

        if not shift:
            raise ValueError("Shift not found")

        dispute = Dispute(
            shift_id=shift_id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            dispute_type=dispute_type,
            status="OPEN",
            amount_claimed=amount_claimed,
            notes=notes,
        )

        db.add(dispute)
        await db.commit()
        await db.refresh(dispute)
        return dispute

    @staticmethod
    async def auto_no_show(db: AsyncSession, shift_id: int) -> dict:
        shift = (
            await db.execute(select(Shift).where(Shift.id == shift_id))
        ).scalar_one_or_none()

        if not shift:
            raise ValueError("Shift not found")

        if shift.status != ShiftStatus.ASSIGNED:
            raise ValueError(f"Shift is not ASSIGNED. Current status: {shift.status}")

        if shift.check_in_time is not None:
            raise ValueError("Doctor has already checked in. Cannot mark as no-show.")

        existing = (
            await db.execute(
                select(Dispute).where(
                    Dispute.shift_id == shift_id,
                    Dispute.dispute_type == "NO_SHOW",
                    Dispute.status.notin_(["REJECTED", "RESOLVED"]),
                )
            )
        ).scalars().first()

        if existing:
            return {
                "dispute_id": existing.id,
                "status": existing.status,
                "message": "No-show dispute already exists.",
            }

        amount = float(shift.offered_rate_inr or 0)

        if shift.escrow_status == "HELD":
            dispute = Dispute(
                shift_id=shift_id,
                doctor_id=shift.assigned_doctor_id,
                hospital_id=shift.facility_id,
                dispute_type="NO_SHOW",
                status="REFUNDED",
                amount_claimed=amount,
                amount_refunded=amount,
                notes="Automatic no-show detected before GPS check-in.",
                resolution_notes="Full escrow refunded to hospital.",
                resolved_at=datetime.now(timezone.utc),
            )

            db.add(dispute)

            # Ledger: escrow out, hospital back in
            db.add(
                LedgerEntry(
                    shift_id=shift_id,
                    entity_type="escrow",
                    entity_id=0,
                    amount=-amount,
                    transaction_type="REFUND",
                    notes="Automatic no-show refund from escrow",
                )
            )

            db.add(
                LedgerEntry(
                    shift_id=shift_id,
                    entity_type="hospital",
                    entity_id=shift.facility_id,
                    amount=amount,
                    transaction_type="REFUND_RECEIVED",
                    notes="Automatic no-show refund credited to hospital",
                )
            )

            shift.escrow_status = "REFUNDED"

            await db.commit()
            await db.refresh(dispute)
            await publish_ops_event(shift.facility_id, 'DISPUTE_OPENED', {
                'shift_id': shift.id,
                'doctor_id': shift.assigned_doctor_id,
                'dispute_type': 'NO_SHOW',
                'amount_claimed_inr': amount,
            })
            await publish_ops_event(shift.facility_id, 'REFUND_ISSUED', {
                'shift_id': shift.id,
                'doctor_id': shift.assigned_doctor_id,
                'dispute_id': dispute.id,
                'amount_refunded_inr': amount,
            })

            return {
                "dispute_id": dispute.id,
                "status": dispute.status,
                "refund_amount": amount,
                "message": "Doctor no-show confirmed. Full escrow refunded to hospital.",
            }

        elif shift.escrow_status == "PAID_OUT":
            dispute = Dispute(
                shift_id=shift_id,
                doctor_id=shift.assigned_doctor_id,
                hospital_id=shift.facility_id,
                dispute_type="NO_SHOW",
                status="UNDER_REVIEW",
                amount_claimed=amount,
                amount_refunded=0.0,
                notes="Automatic no-show detected after payout release.",
                resolution_notes="Manual clawback required because escrow was already released.",
            )

            db.add(dispute)
            await db.commit()
            await db.refresh(dispute)

            return {
                "dispute_id": dispute.id,
                "status": dispute.status,
                "refund_amount": 0.0,
                "message": "No-show recorded, but payout already released. Manual clawback required.",
            }

        else:
            dispute = Dispute(
                shift_id=shift_id,
                doctor_id=shift.assigned_doctor_id,
                hospital_id=shift.facility_id,
                dispute_type="NO_SHOW",
                status="OPEN",
                amount_claimed=amount,
                notes="No-show reported, but escrow is not in refundable state.",
            )

            db.add(dispute)
            await db.commit()
            await db.refresh(dispute)

            return {
                "dispute_id": dispute.id,
                "status": dispute.status,
                "refund_amount": 0.0,
                "message": "No-show dispute opened. Escrow is not currently HELD.",
            }

    @staticmethod
    async def resolve_dispute(
        db: AsyncSession,
        dispute_id: int,
        resolution_status: str,
        refund_amount: float | None = None,
        resolution_notes: str | None = None,
    ) -> dict:
        dispute = (
            await db.execute(select(Dispute).where(Dispute.id == dispute_id))
        ).scalar_one_or_none()

        if not dispute:
            raise ValueError("Dispute not found")

        if dispute.status in ["REFUNDED", "PARTIAL_REFUND", "REJECTED", "RESOLVED"]:
            raise ValueError(f"Dispute already resolved with status: {dispute.status}")

        shift = (
            await db.execute(select(Shift).where(Shift.id == dispute.shift_id))
        ).scalar_one_or_none()

        if not shift:
            raise ValueError("Associated shift not found")

        resolution_status = resolution_status.upper()

        if resolution_status in ["REFUNDED", "PARTIAL_REFUND"]:
            amount = float(refund_amount or dispute.amount_claimed or 0)

            if amount <= 0:
                raise ValueError("Refund amount must be greater than zero")

            if shift.escrow_status != "HELD":
                raise ValueError(
                    f"Cannot refund because escrow status is {shift.escrow_status}, not HELD"
                )

            max_refund = float(shift.offered_rate_inr or 0)
            if amount > max_refund:
                raise ValueError(f"Refund amount cannot exceed shift value of {max_refund}")

            dispute.status = resolution_status
            dispute.amount_refunded = amount
            dispute.resolution_notes = resolution_notes
            dispute.resolved_at = datetime.now(timezone.utc)

            db.add(
                LedgerEntry(
                    shift_id=shift.id,
                    entity_type="escrow",
                    entity_id=0,
                    amount=-amount,
                    transaction_type="REFUND",
                    notes=resolution_notes or "Dispute refund from escrow",
                )
            )

            db.add(
                LedgerEntry(
                    shift_id=shift.id,
                    entity_type="hospital",
                    entity_id=dispute.hospital_id or shift.facility_id,
                    amount=amount,
                    transaction_type="REFUND_RECEIVED",
                    notes=resolution_notes or "Dispute refund credited to hospital",
                )
            )

            if amount == max_refund:
                shift.escrow_status = "REFUNDED"
            else:
                shift.escrow_status = "PARTIALLY_REFUNDED"

            await db.commit()
            await db.refresh(dispute)

            return {
                "dispute_id": dispute.id,
                "status": dispute.status,
                "refund_amount": dispute.amount_refunded,
                "message": "Dispute resolved with refund.",
            }

        elif resolution_status == "REJECTED":
            dispute.status = "REJECTED"
            dispute.amount_refunded = 0.0
            dispute.resolution_notes = resolution_notes
            dispute.resolved_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(dispute)

            return {
                "dispute_id": dispute.id,
                "status": dispute.status,
                "refund_amount": 0.0,
                "message": "Dispute rejected. No refund issued.",
            }

        elif resolution_status == "RESOLVED":
            dispute.status = "RESOLVED"
            dispute.resolution_notes = resolution_notes
            dispute.resolved_at = datetime.now(timezone.utc)

            await db.commit()
            await db.refresh(dispute)

            return {
                "dispute_id": dispute.id,
                "status": dispute.status,
                "refund_amount": dispute.amount_refunded or 0.0,
                "message": "Dispute marked resolved without automatic refund.",
            }

        else:
            raise ValueError(f"Unsupported resolution status: {resolution_status}")
