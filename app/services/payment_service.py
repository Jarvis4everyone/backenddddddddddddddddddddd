from typing import Optional, List
from datetime import datetime
from bson import ObjectId
import razorpay
import asyncio
from app.database import db
from app.config import settings
from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Initialize Razorpay client with timeout settings
razorpay_client = razorpay.Client(
    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
)
# Set timeout for requests (30 seconds)
razorpay_client.set_app_details({"title": "Jarvis4Everyone", "version": "1.0.0"})


class PaymentService:
    @staticmethod
    def _create_order_sync(order_data: dict) -> dict:
        """Synchronous Razorpay order creation (called in thread pool)"""
        return razorpay_client.order.create(data=order_data)
    
    @staticmethod
    async def create_order(amount: float, currency: str = "INR") -> dict:
        """Create Razorpay order with retry logic and proper error handling"""
        order_data = {
            "amount": int(amount * 100),  # Convert to paise
            "currency": currency,
            "payment_capture": 1
        }
        
        logger.info(f"[cyan]💳[/cyan] Creating Razorpay order: {amount} {currency}")
        
        # Retry logic with exponential backoff
        max_retries = 3
        delay = 1.0
        backoff = 2.0
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Run synchronous Razorpay call in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                order = await loop.run_in_executor(
                    None, 
                    PaymentService._create_order_sync, 
                    order_data
                )
                
                logger.info(f"[bold green]✓[/bold green] Razorpay order created: {order.get('id')}")
                return order
                
            except razorpay.errors.BadRequestError as e:
                # Don't retry on bad requests (invalid data)
                logger.error(f"[bold red]✗[/bold red] Razorpay bad request error: [red]{str(e)}[/red]")
                raise ValueError(f"Invalid payment request: {str(e)}")
                
            except (ConnectionError, TimeoutError, 
                    razorpay.errors.ServerError,
                    Exception) as e:
                last_exception = e
                
                # Check if it's a retryable error
                is_retryable = isinstance(e, (ConnectionError, TimeoutError, razorpay.errors.ServerError))
                
                if attempt < max_retries - 1 and is_retryable:
                    logger.warning(
                        f"[yellow]⚠[/yellow] Attempt {attempt + 1}/{max_retries} failed: "
                        f"[yellow]{str(e)}[/yellow]. Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff
                else:
                    if isinstance(e, razorpay.errors.ServerError):
                        logger.error(f"[bold red]✗[/bold red] Razorpay server error: [red]{str(e)}[/red]")
                        raise ConnectionError(f"Razorpay service unavailable: {str(e)}")
                    elif isinstance(e, (ConnectionError, TimeoutError)):
                        logger.error(f"[bold red]✗[/bold red] Connection error: [red]{str(e)}[/red]")
                        raise ConnectionError(f"Failed to connect to Razorpay: {str(e)}")
                    else:
                        logger.error(f"[bold red]✗[/bold red] Unexpected error: [red]{str(e)}[/red]")
                        raise Exception(f"Failed to create payment order: {str(e)}")
        
        # If we exhausted all retries
        if last_exception:
            logger.error(
                f"[bold red]✗[/bold red] All {max_retries} attempts failed: "
                f"[red]{str(last_exception)}[/red]"
            )
            raise ConnectionError(f"Failed to create payment order after {max_retries} attempts: {str(last_exception)}")

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

