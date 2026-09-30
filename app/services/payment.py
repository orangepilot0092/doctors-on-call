"""
Razorpay Payment Gateway Integration
Docs: https://razorpay.com/docs/payments/
"""
import razorpay
import hmac
import hashlib
from typing import Dict, Optional
from app.core.config import get_settings

settings = get_settings()

# Initialize Razorpay client
# Get keys from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID = "rzp_test_YOUR_KEY_ID"       # Replace with test key
RAZORPAY_KEY_SECRET = "YOUR_KEY_SECRET"         # Replace with test secret

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


class PaymentService:
    """Handles all Razorpay payment operations"""
    
    async def create_customer(self, name: str, email: str, phone: str) -> str:
        """Create Razorpay customer for subscription billing"""
        try:
            customer = razorpay_client.customer.create({
                "name": name,
                "email": email,
                "contact": phone,
                "notes": {
                    "source": "doctors_on_call",
                    "created_by": "platform"
                }
            })
            return customer["id"]
        except Exception as e:
            print(f"❌ Razorpay customer creation failed: {e}")
            raise
    
    async def create_order(self, amount_paise: int, subscription_id: str) -> Dict:
        """Create payment order for one-time charges"""
        try:
            order = razorpay_client.order.create({
                "amount": amount_paise,  # In paise (₹1 = 100 paise)
                "currency": "INR",
                "receipt": f"doc_{subscription_id[:8]}",
                "payment_capture": 1,
                "notes": {
                    "subscription_id": subscription_id,
                    "product": "doctors_on_call_subscription"
                }
            })
            return order
        except Exception as e:
            print(f"❌ Razorpay order creation failed: {e}")
            raise
    
    async def create_subscription(self, customer_id: str, plan_id: str, 
                                  total_count: int = 12) -> Dict:
        """Create recurring subscription"""
        try:
            # First, create a Razorpay plan
            plan = razorpay_client.plan.create({
                "period": "monthly",
                "interval": 1,
                "item": {
                    "name": "Doctors On Call Subscription",
                    "amount": 199900,  # Will be set per plan
                    "currency": "INR"
                }
            })
            
            # Then create subscription against the plan
            subscription = razorpay_client.subscription.create({
                "plan_id": plan["id"],
                "customer_id": customer_id,
                "total_count": total_count,
                "quantity": 1,
                "notes": {
                    "subscription_id": plan_id
                }
            })
            return subscription
        except Exception as e:
            print(f"❌ Razorpay subscription creation failed: {e}")
            raise
    
    async def verify_payment_signature(self, order_id: str, 
                                       payment_id: str, 
                                       signature: str) -> bool:
        """Verify payment signature to prevent fraud"""
        try:
            generated_signature = hmac.new(
                RAZORPAY_KEY_SECRET.encode(),
                f"{order_id}|{payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            return generated_signature == signature
        except Exception as e:
            print(f"❌ Signature verification failed: {e}")
            return False
    
    async def fetch_payment(self, payment_id: str) -> Dict:
        """Get payment details"""
        try:
            return razorpay_client.payment.fetch(payment_id)
        except Exception as e:
            print(f"❌ Payment fetch failed: {e}")
            raise
    
    async def create_refund(self, payment_id: str, amount_paise: Optional[int] = None) -> Dict:
        """Refund a payment (full or partial)"""
        try:
            refund_data = {"payment_id": payment_id}
            if amount_paise:
                refund_data["amount"] = amount_paise
            
            return razorpay_client.refund.create(refund_data)
        except Exception as e:
            print(f"❌ Refund failed: {e}")
            raise


# Singleton
payment_service = PaymentService()
