from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import razorpay
from app.database import db
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


class PaymentService:
    @staticmethod
    async def create_order(amount: float, currency: str = "INR") -> dict:
        """Create Razorpay order"""
        order_data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": currency,
            "payment_capture": 1
        }
        order = razorpay_client.order.create(data=order_data)
        return order

    @staticmethod
    async def create_payment_record(user_id: str, email: str, amount: float, currency: str, razorpay_order_id: str) -> dict:
        """Create payment record in database"""
        payment = {
            "user_id": ObjectId(user_id),
            "email": email,
            "plan_id": "monthly",
            "amount": amount,
            "currency": currency,
            "razorpay_order_id": razorpay_order_id,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        result = await db.database.payments.insert_one(payment)
        payment = await db.database.payments.find_one({"_id": result.inserted_id})
        payment["id"] = str(payment["_id"])
        if payment.get("user_id"):
            payment["user_id"] = str(payment["user_id"])
        return payment

    @staticmethod
    async def verify_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
        """Verify Razorpay payment signature"""
        try:
            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)
            return True
        except Exception as e:
            logger.error(f"[bold red]✗[/bold red] Payment verification failed for order {razorpay_order_id}: [red]{str(e)}[/red]")
            return False

    @staticmethod
    async def update_payment_status(
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        status: str
    ) -> Optional[dict]:
        """Update payment status after verification"""
        payment = await db.database.payments.find_one({"razorpay_order_id": razorpay_order_id})
        if not payment:
            return None
        
        update_data = {
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
            "status": status
        }
        
        await db.database.payments.update_one(
            {"_id": payment["_id"]},
            {"$set": update_data}
        )
        
        payment = await db.database.payments.find_one({"_id": payment["_id"]})
        payment["id"] = str(payment["_id"])
        if payment.get("user_id"):
            payment["user_id"] = str(payment["user_id"])
        return payment

    @staticmethod
    async def get_payment_by_order_id(razorpay_order_id: str) -> Optional[dict]:
        """Get payment by Razorpay order ID"""
        payment = await db.database.payments.find_one({"razorpay_order_id": razorpay_order_id})
        if payment:
            payment["id"] = str(payment["_id"])
            if payment.get("user_id"):
                payment["user_id"] = str(payment["user_id"])
        return payment

    @staticmethod
    async def get_all_payments(skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all payments (for admin)"""
        payments = []
        async for payment in db.database.payments.find().sort("created_at", -1).skip(skip).limit(limit):
            payment["id"] = str(payment["_id"])
            if payment.get("user_id"):
                payment["user_id"] = str(payment["user_id"])
            payments.append(payment)
        return payments

    @staticmethod
    async def verify_webhook_signature(payload: str, signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            razorpay_client.utility.verify_webhook_signature(payload, signature, settings.razorpay_webhook_secret)
            return True
        except Exception as e:
            logger.error(f"[bold red]✗[/bold red] Webhook signature verification failed: [red]{str(e)}[/red]")
            return False

