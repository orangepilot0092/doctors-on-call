
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.db.session import get_db
from app.services.invoice_service import InvoiceService
from app.models.invoice import Invoice

router = APIRouter(prefix="/compliance", tags=["Invoicing & Tax Compliance"])

@router.post("/shifts/{shift_id}/generate-invoices")
async def generate_invoices(shift_id: int, hospital_id: int, doctor_id: int, db: AsyncSession = Depends(get_db)):
    try:
        res = await InvoiceService.generate_compliance_records(db, shift_id, hospital_id, doctor_id)
        return {"message": "GST and TDS compliance records generated successfully.", "details": res}
    except Exception as e:
        raise HTTPException(400, str(e))

@router.get("/shifts/{shift_id}/invoices")
async def get_shift_invoices(shift_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Invoice).where(Invoice.shift_id == shift_id)
    result = await db.execute(stmt)
    invoices = result.scalars().all()
    return {"shift_id": shift_id, "invoices": [
        {
            "type": i.invoice_type,
            "entity_id": i.entity_id,
            "number": i.invoice_number,
            "base": i.base_amount,
            "gst": i.gst_amount,
            "tds": i.tds_amount,
            "final": i.final_amount
        } for i in invoices
    ]}
