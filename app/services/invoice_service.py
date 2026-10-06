
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.shift import Shift
from app.models.facility import Facility
from app.models.doctor_master_record import Doctor
from app.models.invoice import Invoice
from app.models.ledger import LedgerEntry

class InvoiceService:
    GST_RATE = 0.18  # 18% GST on platform services
    TDS_RATE = 0.02  # 2% TDS on professional fees (Section 194J)

    @staticmethod
    async def generate_compliance_records(db: AsyncSession, shift_id: int, hospital_id: int, doctor_id: int):
        shift = (await db.execute(select(Shift).where(Shift.id == shift_id))).scalar_one_or_none()
        if not shift: raise ValueError("Shift not found")
        if shift.escrow_status != "PAID_OUT": raise ValueError("Shift must be PAID_OUT before generating final invoices")
        
        total_amount = float(shift.offered_rate_inr)
        platform_fee = total_amount * 0.10
        doctor_payout = total_amount - platform_fee
        
        # 1. Platform Fee Invoice (with 18% GST)
        platform_gst = platform_fee * InvoiceService.GST_RATE
        platform_final = platform_fee + platform_gst
        platform_inv_num = f"INV-PLAT-{uuid.uuid4().hex[:8].upper()}"
        
        db.add(Invoice(
            shift_id=shift_id, invoice_type="PLATFORM_FEE", entity_id=hospital_id,
            base_amount=platform_fee, gst_amount=platform_gst, tds_amount=0.0,
            final_amount=platform_final, invoice_number=platform_inv_num
        ))
        
        # Log GST collection in Ledger
        db.add(LedgerEntry(
            shift_id=shift_id, entity_type="platform", entity_id=0, 
            amount=platform_gst, transaction_type="GST_COLLECTED", notes=f"Inv: {platform_inv_num}"
        ))
        
        # 2. Doctor Payout Invoice (with 2% TDS deduction)
        doctor_tds = doctor_payout * InvoiceService.TDS_RATE
        doctor_final = doctor_payout - doctor_tds
        doctor_inv_num = f"INV-DOC-{uuid.uuid4().hex[:8].upper()}"
        
        db.add(Invoice(
            shift_id=shift_id, invoice_type="DOCTOR_PAYOUT", entity_id=doctor_id,
            base_amount=doctor_payout, gst_amount=0.0, tds_amount=doctor_tds,
            final_amount=doctor_final, invoice_number=doctor_inv_num
        ))
        
        # Log TDS deduction in Ledger
        db.add(LedgerEntry(
            shift_id=shift_id, entity_type="doctor", entity_id=doctor_id, 
            amount=-doctor_tds, transaction_type="TDS_DEDUCTED", notes=f"Inv: {doctor_inv_num}"
        ))
        
        await db.commit()
        
        return {
            "platform_invoice": {
                "number": platform_inv_num,
                "base": platform_fee,
                "gst": platform_gst,
                "total": platform_final
            },
            "doctor_invoice": {
                "number": doctor_inv_num,
                "base": doctor_payout,
                "tds_deducted": doctor_tds,
                "net_payout": doctor_final
            }
        }
