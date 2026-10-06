
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.shift import Shift, ShiftStatus
from app.models.doctor_master_record import Doctor
from app.models.ledger import LedgerEntry

class MockRazorpayXClient:
    async def create_fund_account(self, doctor_id: int, name: str, ifsc: str, account: str) -> str:
        # Simulates RazorpayX creating a virtual fund account for the doctor
        return f"fa_MOCK_{doctor_id}_XYZ"
        
    async def trigger_payout(self, fund_account_id: str, amount: float, purpose: str) -> str:
        # Simulates instant NEFT/IMPS transfer to doctor's bank
        return f"payout_MOCK_{int(amount)}_ABC"

razorpayx = MockRazorpayXClient()

class PayoutService:
    @staticmethod
    async def process_instant_payout(db: AsyncSession, shift_id: int, doctor_id: int):
        # 1. Fetch Shift and Doctor
        shift = (await db.execute(select(Shift).where(Shift.id == shift_id))).scalar_one_or_none()
        if not shift: raise ValueError("Shift not found")
        if shift.status != ShiftStatus.COMPLETED: raise ValueError("Shift must be COMPLETED to trigger payout")
        if shift.escrow_status != "HELD": raise ValueError("Escrow must be HELD before payout")
        
        doctor = (await db.execute(select(Doctor).where(Doctor.id == doctor_id))).scalar_one_or_none()
        if not doctor or not doctor.bank_ifsc_code or not doctor.bank_account_number:
            raise ValueError("Doctor bank details missing. Cannot process payout.")
            
        total_amount = float(shift.offered_rate_inr)
        platform_fee_pct = 0.10
        fee = total_amount * platform_fee_pct
        doctor_payout = total_amount - fee
        
        # 2. Simulate RazorpayX Flow
        fund_account_id = await razorpayx.create_fund_account(
            doctor_id=doctor.id,
            name=doctor.bank_holder_name or doctor.full_name,
            ifsc=doctor.bank_ifsc_code,
            account=doctor.bank_account_number
        )
        
        payout_id = await razorpayx.trigger_payout(
            fund_account_id=fund_account_id,
            amount=doctor_payout,
            purpose=f"Locum Shift Payout #{shift_id}"
        )
        
        # 3. Update Ledger (Double-Entry)
        db.add(LedgerEntry(shift_id=shift_id, entity_type="escrow", entity_id=0, amount=-total_amount, transaction_type="RELEASE"))
        db.add(LedgerEntry(shift_id=shift_id, entity_type="platform", entity_id=0, amount=fee, transaction_type="FEE"))
        db.add(LedgerEntry(shift_id=shift_id, entity_type="doctor", entity_id=doctor_id, amount=doctor_payout, transaction_type="PAYOUT", razorpay_id=payout_id, notes=f"Fund Account: {fund_account_id}"))
        
        # 4. Update Shift Status
        shift.escrow_status = "PAID_OUT"
        await db.commit()
        
        return {
            "status": "PAID_OUT",
            "doctor_payout": doctor_payout,
            "platform_fee": fee,
            "razorpay_payout_id": payout_id,
            "fund_account_id": fund_account_id
        }
