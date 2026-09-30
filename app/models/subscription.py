"""
Subscription & Billing Models for Pre-Seed Monetization
"""
import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Enum as SAEnum, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.database import Base


class PlanTier(str, enum.Enum):
    STARTER = "starter"              # ₹1,999/mo - Solo clinics
    CLINIC_PRO = "clinic_pro"        # ₹4,999/mo - Polyclinics
    NURSING_HOME = "nursing_home"    # ₹12,999/mo - 10-30 beds
    HOSPITAL_BASIC = "hospital_basic" # ₹29,999/mo - 30-100 beds
    HOSPITAL_PRO = "hospital_pro"    # ₹79,999/mo - 100-300 beds
    ENTERPRISE = "enterprise"         # Custom - 300+ beds


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"                  # 14-day free trial
    ACTIVE = "active"                # Paid & active
    PAST_DUE = "past_due"            # Payment failed
    CANCELLED = "cancelled"          # Cancelled by user
    EXPIRED = "expired"              # Trial ended


class PaymentStatus(str, enum.Enum):
    CREATED = "created"              # Payment initiated
    AUTHORIZED = "authorized"        # Payment authorized
    CAPTURED = "captured"            # Payment successful
    FAILED = "failed"                # Payment failed
    REFUNDED = "refunded"            # Refunded


class SubscriptionPlan(Base):
    """Pricing tiers - seeded with the 6 plans"""
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tier = Column(SAEnum(PlanTier), nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # Pricing (in INR paise for precision)
    monthly_price = Column(Integer, nullable=False)  # e.g., 199900 = ₹1,999
    annual_price = Column(Integer, nullable=True)    # 2 months free
    per_shift_fee = Column(Integer, nullable=False)  # e.g., 19900 = ₹199
    
    # Usage limits
    included_shifts = Column(Integer, nullable=False)
    max_doctors = Column(Integer, nullable=True)
    max_clinics = Column(Integer, default=1)
    
    # Features (JSON list)
    features = Column(JSONB, default=list)
    
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)  # "Most Popular" badge
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClinicSubscription(Base):
    """Each clinic's active subscription"""
    __tablename__ = "clinic_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clinic_name = Column(String, nullable=False)
    clinic_phone = Column(String, nullable=False)
    clinic_email = Column(String, nullable=True)
    clinic_pincode = Column(String, nullable=False)
    
    # Plan details
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(SAEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    
    # Billing cycle
    billing_cycle = Column(String, default="monthly")  # monthly/annual
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Razorpay customer ID
    razorpay_customer_id = Column(String, nullable=True)
    razorpay_subscription_id = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Payment(Base):
    """Every payment transaction"""
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("clinic_subscriptions.id"), nullable=False)
    
    # Payment details
    amount = Column(Integer, nullable=False)  # In paise
    currency = Column(String, default="INR")
    
    # Razorpay IDs
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.CREATED)
    payment_method = Column(String, nullable=True)  # upi/card/netbanking
    
    metadata = Column(JSONB, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ShiftUsage(Base):
    """Track shift usage against subscription limits"""
    __tablename__ = "shift_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("clinic_subscriptions.id"), nullable=False)
    shift_id = Column(UUID(as_uuid=True), nullable=False)  # Links to shift_requests
    
    # Usage period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Overage billing
    is_overage = Column(Boolean, default=False)
    overage_fee = Column(Integer, default=0)  # Extra charge per shift
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
