
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.shift import Shift, ShiftStatus
from app.models.ledger import LedgerEntry
from app.services.ops_events import publish_ops_event

class MockRazorpayClient:
    async def create_payment(self, amount: float, notes: str) -> str:
        # Simulates Razorpay API returning a payment ID
        return f"pay_MOCK_{int(amount)}_XYZ123"
        
    async def transfer_funds(self, amount: float, to_account: str) -> str:
        # Simulates RazorpayX payout to doctor's bank
        return f"trf_MOCK_{int(amount)}_ABC987"

razorpay = MockRazorpayClient()

class EscrowService:
    @staticmethod
    async def hospital_pays_escrow(db: AsyncSession, shift_id: int, hospital_id: int):
        shift = (await db.execute(select(Shift).where(Shift.id == shift_id))).scalar_one_or_none()
        if not shift: raise ValueError("Shift not found")
        if shift.escrow_status != "UNPAID": raise ValueError("Escrow already funded")
        
        amount = float(shift.offered_rate_inr)
        rp_id = await razorpay.create_payment(amount, f"Shift {shift_id}")
        
        # 1. Log Hospital Debit
        db.add(LedgerEntry(shift_id=shift_id, entity_type="hospital", entity_id=hospital_id, amount=-amount, transaction_type="PAYMENT", razorpay_id=rp_id))
        # 2. Log Escrow Hold
        db.add(LedgerEntry(shift_id=shift_id, entity_type="escrow", entity_id=0, amount=amount, transaction_type="HOLD", razorpay_id=rp_id))
        
        shift.escrow_status = "HELD"
        shift.razorpay_payment_id = rp_id
        await db.commit()
        await publish_ops_event(shift.facility_id, 'ESCROW_FUNDED', {
            'shift_id': shift.id,
            'amount_inr': amount,
            'razorpay_id': rp_id,
        })
        return {"status": "HELD", "razorpay_id": rp_id, "amount": amount}

    @staticmethod
    async def release_escrow_to_doctor(db: AsyncSession, shift_id: int, doctor_id: int, platform_fee_pct: float = 0.10):
        shift = (await db.execute(select(Shift).where(Shift.id == shift_id))).scalar_one_or_none()
        if not shift: raise ValueError("Shift not found")
        if shift.escrow_status != "HELD": raise ValueError("Escrow not in HELD state")
        if shift.status != ShiftStatus.COMPLETED: raise ValueError("Shift must be COMPLETED (checked out) to release funds")
        
        total_amount = float(shift.offered_rate_inr)
        fee = total_amount * platform_fee_pct
        doctor_payout = total_amount - fee
        
        # 1. Log Escrow Release
        db.add(LedgerEntry(shift_id=shift_id, entity_type="escrow", entity_id=0, amount=-total_amount, transaction_type="RELEASE"))
        # 2. Log Platform Fee
        db.add(LedgerEntry(shift_id=shift_id, entity_type="platform", entity_id=0, amount=fee, transaction_type="FEE"))
        # 3. Log Doctor Payout
        trf_id = await razorpay.transfer_funds(doctor_payout, f"doctor_{doctor_id}_bank")
        db.add(LedgerEntry(shift_id=shift_id, entity_type="doctor", entity_id=doctor_id, amount=doctor_payout, transaction_type="PAYOUT", razorpay_id=trf_id))
        
        shift.escrow_status = "RELEASED"
        await db.commit()
        await publish_ops_event(shift.facility_id, 'ESCROW_RELEASED', {
            'shift_id': shift.id,
            'doctor_payout': doctor_payout,
            'platform_fee': fee,
        })
        return {"status": "RELEASED", "doctor_payout": doctor_payout, "platform_fee": fee}
