from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.hospital_admin import HospitalAdmin
from app.models.shift import Shift, ShiftStatus
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_admin
from app.schemas.shift import ShiftRead

router = APIRouter(prefix="/portal", tags=["Hospital Web Portal"])

# --- Schemas ---
class AdminRegister(BaseModel):
    email: EmailStr
    password: str
    facility_id: int # Must be a valid ID from our 35k OSM/Commercial DB

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Auth Endpoints ---
@router.post("/register", status_code=201)
async def register_admin(data: AdminRegister, db: AsyncSession = Depends(get_db)):
    # Check if admin exists
    result = await db.execute(select(HospitalAdmin).where(HospitalAdmin.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_admin = HospitalAdmin(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        facility_id=data.facility_id
    )
    db.add(new_admin)
    await db.commit()
    return {"message": "Admin registered successfully. Please log in."}

@router.post("/login", response_model=Token)
async def login_admin(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HospitalAdmin).where(HospitalAdmin.email == form_data.username))
    admin = result.scalar_one_or_none()
    
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": admin.email, "facility_id": admin.facility_id})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Roster & Shift Lifecycle Endpoints ---
@router.get("/shifts", response_model=List[ShiftRead])
async def get_my_hospital_shifts(
    email: str = Depends(get_current_admin), 
    db: AsyncSession = Depends(get_db)
):
    # Get admin to find facility_id
    result = await db.execute(select(HospitalAdmin).where(HospitalAdmin.email == email))
    admin = result.scalar_one()
    
    # Fetch shifts for this specific facility
    shifts_result = await db.execute(
        select(Shift).where(Shift.facility_id == admin.facility_id).order_by(Shift.start_time.desc())
    )
    return shifts_result.scalars().all()

@router.post("/shifts/{shift_id}/assign")
async def assign_shift(
    shift_id: int, 
    doctor_hpr_id: str,
    email: str = Depends(get_current_admin), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift: raise HTTPException(status_code=404, detail="Shift not found")
    
    shift.status = ShiftStatus.ASSIGNED
    # In a real app, we'd link the doctor_hpr_id to the shift here
    await db.commit()
    return {"message": f"Shift {shift_id} assigned to HPR {doctor_hpr_id}", "status": shift.status}

@router.post("/shifts/{shift_id}/cancel")
async def cancel_shift(
    shift_id: int, 
    email: str = Depends(get_current_admin), 
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Shift).where(Shift.id == shift_id))
    shift = result.scalar_one_or_none()
    if not shift: raise HTTPException(status_code=404, detail="Shift not found")
    
    shift.status = ShiftStatus.CANCELLED
    await db.commit()
    return {"message": f"Shift {shift_id} cancelled", "status": shift.status}
