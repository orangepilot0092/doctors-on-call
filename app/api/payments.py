
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.services.escrow_service import EscrowService
from app.models.ledger import LedgerEntry

router = APIRouter(prefix="/payments", tags=["Financials & Escrow"])

@router.post("/shifts/{shift_id}/fund-escrow")
async def fund_escrow(shift_id: int, hospital_id: int = 4, db: AsyncSession = Depends(get_db)):
    try:
        res = await EscrowService.hospital_pays_escrow(db, shift_id, hospital_id)
        return {"message": "Hospital payment successful. Funds held in Escrow.", "details": res}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.post("/shifts/{shift_id}/release-escrow")
async def release_escrow(shift_id: int, doctor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        res = await EscrowService.release_escrow_to_doctor(db, shift_id, doctor_id)
        return {"message": "Funds released to doctor.", "details": res}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/shifts/{shift_id}/ledger")
async def get_ledger(shift_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(LedgerEntry).where(LedgerEntry.shift_id == shift_id).order_by(LedgerEntry.created_at)
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {"shift_id": shift_id, "ledger": [
        {"entity": e.entity_type, "type": e.transaction_type, "amount": e.amount, "rp_id": e.razorpay_id} for e in entries
    ]}
