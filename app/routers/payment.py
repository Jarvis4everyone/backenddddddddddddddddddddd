from fastapi import APIRouter, Depends, HTTPException, status, Request
from app.schemas.payment import PaymentCreate, PaymentVerify, PaymentResponse
from app.services.payment_service import PaymentService
from app.services.subscription_service import SubscriptionService
from app.middleware.auth import get_current_user
from app.config import settings
from app.utils.logging_config import get_logger
import json

logger = get_logger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-order", response_model=dict)
async def create_payment_order(
    payment_data: PaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create Razorpay order for payment"""
    # Create Razorpay order
    order = await PaymentService.create_order(payment_data.amount, payment_data.currency)
    
    # Create payment record
    payment = await PaymentService.create_payment_record(
        current_user["id"],
        current_user["email"],
        payment_data.amount,
        payment_data.currency,
        order["id"]
    )
    
    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": settings.razorpay_key_id,
        "payment_id": payment["id"]
    }


@router.post("/verify", response_model=PaymentResponse)
async def verify_payment(
    verify_data: PaymentVerify,
    current_user: dict = Depends(get_current_user)
):
    """Verify Razorpay payment and activate subscription"""
    # Get payment record
    payment = await PaymentService.get_payment_by_order_id(verify_data.razorpay_order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found"
        )
    
    # Verify payment belongs to current user
    if payment.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Payment does not belong to current user"
        )
    
    # Verify payment signature
    is_valid = await PaymentService.verify_payment(
        verify_data.razorpay_order_id,
        verify_data.razorpay_payment_id,
        verify_data.razorpay_signature
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payment signature"
        )
    
    # Update payment status
    payment = await PaymentService.update_payment_status(
        verify_data.razorpay_order_id,
        verify_data.razorpay_payment_id,
        verify_data.razorpay_signature,
        "completed"
    )
    
    # Activate subscription (1 month for now)
    await SubscriptionService.renew_subscription(current_user["id"], 1)
    
    return payment


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    """Handle Razorpay webhook (for payment status updates)"""
    # Get webhook signature from headers
    signature = request.headers.get("X-Razorpay-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing webhook signature"
        )
    
    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Verify webhook signature
    is_valid = await PaymentService.verify_webhook_signature(body_str, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Parse webhook payload
    try:
        payload = json.loads(body_str)
        event = payload.get("event")
        
        if event == "payment.captured":
            # Payment successful
            payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_data.get("order_id")
            
            if order_id:
                payment = await PaymentService.get_payment_by_order_id(order_id)
                if payment and payment["status"] == "pending":
                    await PaymentService.update_payment_status(
                        order_id,
                        payment_data.get("id", ""),
                        signature,
                        "completed"
                    )
                    
                    # Activate subscription if user exists
                    if payment.get("user_id"):
                        await SubscriptionService.renew_subscription(str(payment["user_id"]), 1)
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"[bold red]✗[/bold red] Webhook processing error: [red]{str(e)}[/red]")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

