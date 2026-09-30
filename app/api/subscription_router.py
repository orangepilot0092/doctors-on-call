"""
Subscription & Billing API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import json

from app.db.database import get_db
from app.models.subscription import (
    SubscriptionPlan,
    ClinicSubscription,
    Payment,
    PlanTier,
    SubscriptionStatus,
    PaymentStatus,
)
from app.services.payment import payment_service
from app.services.whatsapp_real import whatsapp_service

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])


# ==================== PLANS ====================

@router.get("/plans", response_model=List[dict])
async def get_plans(db: AsyncSession = Depends(get_db)):
    """Get all available pricing plans"""
    result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.monthly_price)
    )
    plans = result.scalars().all()
    
    return [
        {
            "id": str(plan.id),
            "tier": plan.tier.value,
            "name": plan.name,
            "description": plan.description,
            "monthly_price": plan.monthly_price / 100,  # Convert paise to INR
            "annual_price": plan.annual_price / 100 if plan.annual_price else None,
            "per_shift_fee": plan.per_shift_fee / 100,
            "included_shifts": plan.included_shifts,
            "max_doctors": plan.max_doctors,
            "features": plan.features,
            "is_popular": plan.is_popular
        }
        for plan in plans
    ]


@router.post("/plans/seed")
async def seed_plans(db: AsyncSession = Depends(get_db)):
    """Seed the 6 pricing tiers"""
    
    plans_data = [
        {
            "tier": PlanTier.STARTER,
            "name": "Starter",
            "description": "Perfect for solo clinics",
            "monthly_price": 199900,  # ₹1,999
            "annual_price": 19990,    # 2 months free
            "per_shift_fee": 19900,   # ₹199
            "included_shifts": 5,
            "max_doctors": 50,
            "features": [
                "5 shifts/month included",
                "AI doctor matching",
                "WhatsApp notifications",
                "Email support"
            ],
            "is_popular": False
        },
        {
            "tier": PlanTier.CLINIC_PRO,
            "name": "Clinic Pro",
            "description": "For growing polyclinics",
            "monthly_price": 499900,  # ₹4,999
            "annual_price": 49990,
            "per_shift_fee": 14900,   # ₹149
            "included_shifts": 15,
            "max_doctors": 150,
            "features": [
                "15 shifts/month included",
                "AI doctor matching",
                "WhatsApp notifications",
                "Priority support",
                "Analytics dashboard"
            ],
            "is_popular": True  # Most Popular badge
        },
        {
            "tier": PlanTier.NURSING_HOME,
            "name": "Nursing Home",
            "description": "For 10-30 bed facilities",
            "monthly_price": 1299900,  # ₹12,999
            "annual_price": 129990,
            "per_shift_fee": 9900,     # ₹99
            "included_shifts": 40,
            "max_doctors": 400,
            "features": [
                "40 shifts/month included",
                "Multi-doctor coordination",
                "NABH-ready reports",
                "Phone support",
                "Custom branding"
            ],
            "is_popular": False
        },
        {
            "tier": PlanTier.HOSPITAL_BASIC,
            "name": "Hospital Basic",
            "description": "For 30-100 bed hospitals",
            "monthly_price": 2999900,  # ₹29,999
            "annual_price": 299990,
            "per_shift_fee": 7900,     # ₹79
            "included_shifts": 100,
            "max_doctors": 1000,
            "features": [
                "100 shifts/month included",
                "Multi-department management",
                "Compliance dashboard",
                "Dedicated account manager",
                "API access"
            ],
            "is_popular": False
        },
        {
            "tier": PlanTier.HOSPITAL_PRO,
            "name": "Hospital Pro",
            "description": "For 100-300 bed hospitals",
            "monthly_price": 7999900,  # ₹79,999
            "annual_price": 799990,
            "per_shift_fee": 4900,     # ₹49
            "included_shifts": 300,
            "max_doctors": 3000,
            "features": [
                "300 shifts/month included",
                "Enterprise integrations",
                "White-label option",
                "24/7 dedicated support",
                "Custom SLA"
            ],
            "is_popular": False
        },
        {
            "tier": PlanTier.ENTERPRISE,
            "name": "Enterprise",
            "description": "For 300+ bed multi-location chains",
            "monthly_price": 0,  # Custom pricing
            "annual_price": 0,
            "per_shift_fee": 2900,  # ₹29
            "included_shifts": 9999,
            "max_doctors": 99999,
            "features": [
                "Unlimited shifts",
                "Multi-location management",
                "Custom integrations",
                "Dedicated success team",
                "Custom SLA & pricing"
            ],
            "is_popular": False
        }
    ]
    
    created_plans = []
    for plan_data in plans_data:
        # Check if plan already exists
        existing = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.tier == plan_data["tier"])
        )
        if not existing.scalar_one_or_none():
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)
            created_plans.append(plan_data["tier"].value)
    
    await db.commit()
    
    return {
        "message": f"Seeded {len(created_plans)} plans",
        "plans": created_plans
    }


# ==================== SUBSCRIPTIONS ====================

@router.post("/subscribe")
async def create_subscription(
    clinic_name: str,
    clinic_phone: str,
    clinic_email: str,
    clinic_pincode: str,
    plan_tier: str,
    billing_cycle: str = "monthly",
    db: AsyncSession = Depends(get_db)
):
    """Create a new clinic subscription"""
    
    # Get plan
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.tier == PlanTier(plan_tier))
    )
    plan = plan_result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Check if clinic already has active subscription
    existing = await db.execute(
        select(ClinicSubscription).where(
            ClinicSubscription.clinic_phone == clinic_phone,
            ClinicSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Clinic already has active subscription")
    
    # Create subscription with 14-day trial
    subscription = ClinicSubscription(
        clinic_name=clinic_name,
        clinic_phone=clinic_phone,
        clinic_email=clinic_email,
        clinic_pincode=clinic_pincode,
        plan_id=plan.id,
        status=SubscriptionStatus.TRIAL,
        billing_cycle=billing_cycle,
        trial_ends_at=datetime.utcnow() + timedelta(days=14),
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=14),
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    
    # Send welcome WhatsApp
    await whatsapp_service.send_text_message(
        clinic_phone,
        f"""🎉 *Welcome to DOCTORS ON CALL!*

Hi {clinic_name},

Your {plan.name} plan has been activated with a 14-day free trial.

📋 Plan: {plan.name}
📅 Trial ends: {subscription.trial_ends_at.strftime('%d %B %Y')}

You can request unlimited shifts during your trial!

Need help? Reply to this message.

- Team DOCTORS ON CALL"""
    )
    
    return {
        "subscription_id": str(subscription.id),
        "status": subscription.status.value,
        "trial_ends_at": subscription.trial_ends_at.isoformat(),
        "message": "Subscription created with 14-day free trial"
    }


@router.post("/checkout")
async def checkout_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create Razorpay order for subscription payment"""
    
    # Get subscription
    sub_result = await db.execute(
        select(ClinicSubscription).where(ClinicSubscription.id == uuid.UUID(subscription_id))
    )
    subscription = sub_result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Get plan
    plan_result = await db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    
    # Calculate amount
    if subscription.billing_cycle == "monthly":
        amount = plan.monthly_price
    else:
        amount = plan.annual_price
    
    # Create Razorpay order
    order = await payment_service.create_order(amount, str(subscription.id))
    
    # Create payment record
    payment = Payment(
        subscription_id=subscription.id,
        amount=amount,
        razorpay_order_id=order["id"],
        status=PaymentStatus.CREATED
    )
    db.add(payment)
    await db.commit()
    
    return {
        "order_id": order["id"],
        "amount": amount,
        "currency": "INR",
        "key_id": "rzp_test_YOUR_KEY_ID",  # Your public key
        "subscription_id": str(subscription.id)
    }


@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Razorpay payment webhooks"""
    
    payload = await request.json()
    
    # Verify webhook signature (important for security)
    signature = request.headers.get("X-Razorpay-Signature")
    # TODO: Verify signature
    
    event = payload.get("event")
    
    if event == "payment.captured":
        # Payment successful
        payment_entity = payload["payload"]["payment"]["entity"]
        payment_id = payment_entity["id"]
        
        # Update payment status
        payment_result = await db.execute(
            select(Payment).where(Payment.razorpay_payment_id == payment_id)
        )
        payment = payment_result.scalar_one_or_none()
        
        if payment:
            payment.status = PaymentStatus.CAPTURED
            payment.updated_at = datetime.utcnow()
            
            # Activate subscription
            sub_result = await db.execute(
                select(ClinicSubscription).where(
                    ClinicSubscription.id == payment.subscription_id
                )
            )
            subscription = sub_result.scalar_one_or_none()
            
            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_start = datetime.utcnow()
                
                # Set period end based on billing cycle
                if subscription.billing_cycle == "monthly":
                    subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                else:
                    subscription.current_period_end = datetime.utcnow() + timedelta(days=365)
                
                await db.commit()
                
                # Send receipt via WhatsApp
                await whatsapp_service.send_payment_receipt(
                    subscription.clinic_phone,
                    subscription.clinic_name,
                    "Monthly Plan",
                    payment.amount / 100,
                    payment_id
                )
    
    elif event == "payment.failed":
        # Payment failed
        payment_entity = payload["payload"]["payment"]["entity"]
        payment_id = payment_entity["id"]
        
        payment_result = await db.execute(
            select(Payment).where(Payment.razorpay_payment_id == payment_id)
        )
        payment = payment_result.scalar_one_or_none()
        
        if payment:
            payment.status = PaymentStatus.FAILED
            await db.commit()
    
    return {"status": "ok"}


# ==================== DASHBOARD ====================

@router.get("/dashboard")
async def subscription_dashboard(db: AsyncSession = Depends(get_db)):
    """Admin dashboard for all subscriptions"""
    
    # Get all subscriptions
    result = await db.execute(
        select(ClinicSubscription).order_by(ClinicSubscription.created_at.desc())
    )
    subscriptions = result.scalars().all()
    
    # Calculate metrics
    total_subscriptions = len(subscriptions)
    active_subscriptions = len([s for s in subscriptions if s.status == SubscriptionStatus.ACTIVE])
    trial_subscriptions = len([s for s in subscriptions if s.status == SubscriptionStatus.TRIAL])
    
    # Calculate MRR (Monthly Recurring Revenue)
    mrr = 0
    for sub in subscriptions:
        if sub.status == SubscriptionStatus.ACTIVE:
            plan_result = await db.execute(
                select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
            )
            plan = plan_result.scalar_one_or_none()
            if plan:
                mrr += plan.monthly_price
    
    return {
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "trial_subscriptions": trial_subscriptions,
        "mrr": mrr / 100,  # Convert to INR
        "arr": (mrr * 12) / 100,  # Annual Recurring Revenue
        "subscriptions": [
            {
                "id": str(s.id),
                "clinic_name": s.clinic_name,
                "clinic_phone": s.clinic_phone,
                "status": s.status.value,
                "trial_ends_at": s.trial_ends_at.isoformat() if s.trial_ends_at else None,
                "created_at": s.created_at.isoformat()
            }
            for s in subscriptions
        ]
    }
