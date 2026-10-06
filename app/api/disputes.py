
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_db
from app.models.dispute import Dispute
from app.services.dispute_service import DisputeService

router = APIRouter(prefix="/disputes", tags=["Dispute Resolution & Refunds"])


class OpenDisputeRequest(BaseModel):
    dispute_type: str
    doctor_id: int | None = None
    hospital_id: int | None = None
    amount_claimed: float | None = None
    notes: str | None = None


class ResolveDisputeRequest(BaseModel):
    resolution_status: str
    refund_amount: float | None = None
    resolution_notes: str | None = None


@router.post("/shifts/{shift_id}/open")
async def open_dispute(shift_id: int, req: OpenDisputeRequest, db: AsyncSession = Depends(get_db)):
    try:
        dispute = await DisputeService.open_dispute(
            db=db,
            shift_id=shift_id,
            dispute_type=req.dispute_type.upper(),
            doctor_id=req.doctor_id,
            hospital_id=req.hospital_id,
            amount_claimed=req.amount_claimed,
            notes=req.notes,
        )
        return {
            "message": "Dispute opened successfully.",
            "dispute_id": dispute.id,
            "status": dispute.status,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/shifts/{shift_id}/auto-no-show")
async def auto_no_show(shift_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await DisputeService.auto_no_show(db=db, shift_id=shift_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: int,
    req: ResolveDisputeRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await DisputeService.resolve_dispute(
            db=db,
            dispute_id=dispute_id,
            resolution_status=req.resolution_status,
            refund_amount=req.refund_amount,
            resolution_notes=req.resolution_notes,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shifts/{shift_id}")
async def list_shift_disputes(shift_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Dispute).where(Dispute.shift_id == shift_id).order_by(Dispute.created_at.desc())
    result = await db.execute(stmt)
    disputes = result.scalars().all()

    return {
        "shift_id": shift_id,
        "disputes": [
            {
                "id": d.id,
                "type": d.dispute_type,
                "status": d.status,
                "doctor_id": d.doctor_id,
                "hospital_id": d.hospital_id,
                "amount_claimed": d.amount_claimed,
                "amount_refunded": d.amount_refunded,
                "notes": d.notes,
                "resolution_notes": d.resolution_notes,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
            }
            for d in disputes
        ],
    }
